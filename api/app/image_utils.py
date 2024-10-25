# api/app/image_utils.py

import requests
import logging
from PIL import Image
from io import BytesIO
from fastapi import HTTPException
from typing import Tuple
from pathlib import Path
from .config import AVATARS_DIR, THUMBNAILS_DIR
from openai import OpenAI, OpenAIError
import base64
import os

logger = logging.getLogger("image_utils")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def download_image(url: str, save_path: Path) -> str:
    """Generic image download function."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.save(save_path)
        return str(save_path)
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download image.")

async def download_avatar_image(user_id: str) -> str:
    """Download and save player avatar image."""
    avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
    try:
        response = requests.get(avatar_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        save_path = AVATARS_DIR / f"{user_id}.png"
        return download_image(image_url, save_path)
    except Exception as e:
        logger.error(f"Error fetching avatar image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download avatar image.")

async def download_asset_image(asset_id: str) -> Tuple[str, str]:
    """Download and save asset thumbnail."""
    asset_api_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
    try:
        response = requests.get(asset_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        save_path = THUMBNAILS_DIR / f"{asset_id}.png"
        local_path = download_image(image_url, save_path)
        return local_path, image_url
    except Exception as e:
        logger.error(f"Error fetching asset image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download asset image.")

async def generate_image_description(
    image_path: str, 
    prompt: str, 
    max_length: int = 300
) -> str:
    """Generate AI description for an image."""
    base64_image = encode_image(image_path)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt} Limit the description to {max_length} characters."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        }
                    ],
                }
            ]
        )
        description = response.choices[0].message.content
        return description
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "No description available."

async def get_asset_description(asset_id: str, name: str) -> dict:
    """Get asset description and image URL."""
    try:
        image_path, image_url = await download_asset_image(asset_id)
        prompt = (
            "Please provide a detailed description of this Roblox asset image. "
            "Include details about its appearance, features, and any notable characteristics."
        )
        ai_description = await generate_image_description(image_path, prompt)
        return {
            "description": ai_description,
            "imageUrl": image_url
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing asset description request: {e}")
        return {"error": f"Failed to process request: {str(e)}"}