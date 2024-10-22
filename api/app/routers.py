import os
import logging
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from typing import Literal, Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAI, OpenAIError
from app.conversation_manager import ConversationManager
from app.config import NPC_SYSTEM_PROMPT_ADDITION
import sys
import subprocess

# Add the utils directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'utils')))

# Import the update_asset_descriptions function
from update_asset_descriptions import update_asset_descriptions, load_json_database, save_json_database, save_lua_database

# OpenAI Client initialization
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths to store images locally
AVATAR_SAVE_PATH = "stored_images"
ASSET_IMAGE_SAVE_PATH = "stored_asset_images"
os.makedirs(AVATAR_SAVE_PATH, exist_ok=True)
os.makedirs(ASSET_IMAGE_SAVE_PATH, exist_ok=True)

# Constants for asset database files
JSON_DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'data', 'AssetDatabase.json'))
LUA_DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'data', 'AssetDatabase.lua'))

# Initialize logging and router
logger = logging.getLogger("ella_app")
router = APIRouter()

# Pydantic Models

class PerceptionData(BaseModel):
    visible_objects: List[str] = Field(default_factory=list)
    visible_players: List[str] = Field(default_factory=list)
    memory: List[Dict[str, Any]] = Field(default_factory=list)

class EnhancedChatMessageV3(BaseModel):
    message: str
    player_id: str
    npc_id: str
    npc_name: str
    system_prompt: str
    perception: Optional[PerceptionData] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    limit: int = 200

class NPCAction(BaseModel):
    type: Literal["follow", "unfollow", "stop_talking", "none"]
    data: Optional[Dict[str, Any]] = None

class NPCResponseV3(BaseModel):
    message: str
    action: NPCAction
    internal_state: Optional[Dict[str, Any]] = None

class PlayerDescriptionRequest(BaseModel):
    user_id: str

class PlayerDescriptionResponse(BaseModel):
    description: str

class AssetData(BaseModel):
    asset_id: str
    name: str

class AssetResponse(BaseModel):
    asset_id: str
    name: str
    description: str
    image_url: str

class UpdateAssetsRequest(BaseModel):
    overwrite: bool = False
    single_asset: Optional[str] = None
    only_empty: bool = False

class EditItemRequest(BaseModel):
    id: str
    description: str

# Initialize conversation manager
conversation_manager = ConversationManager()

# Helper Functions

def encode_image(image_path: str) -> str:
    """
    Encode an image as a base64 string.
    :param image_path: Path to the image file.
    :return: Base64 encoded image string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def download_image(url: str, save_path: str) -> str:
    """
    Download an image from a URL and save it locally.
    :param url: The URL of the image.
    :param save_path: Local path to save the downloaded image.
    :return: The path where the image is saved.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.save(save_path)
        return save_path
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download image.")

def generate_avatar_description_from_image(image_path: str, max_length: int = 300) -> str:
    """
    Generate a description for an avatar using OpenAI's model and the image as base64.
    :param image_path: Path to the image.
    :param max_length: Maximum length of the generated description.
    :return: Generated description.
    """
    base64_image = encode_image(image_path)
    
    # Sending the image to OpenAI API for a detailed description
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Please provide a detailed description of this Roblox avatar within {max_length} characters. "
                                "Include details about the avatar's clothing, accessories, colors, any unique features, and its overall style or theme."
                            ),
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

def download_avatar_image(user_id: str) -> str:
    """
    Download an avatar image from Roblox API and store it.
    :param user_id: Roblox user ID.
    :return: Path to the saved image.
    """
    avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
    try:
        response = requests.get(avatar_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        return download_image(image_url, os.path.join(AVATAR_SAVE_PATH, f"{user_id}.png"))
    except Exception as e:
        logger.error(f"Error fetching avatar image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download avatar image.")

def download_asset_image(asset_id: str) -> tuple[str, str]:
    """
    Download an asset image from Roblox API using the asset ID and store it locally.
    :param asset_id: Asset ID.
    :return: Tuple of (local path where the image is saved, CDN URL of the image).
    """
    asset_api_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
    try:
        response = requests.get(asset_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        local_path = os.path.join(ASSET_IMAGE_SAVE_PATH, f"{asset_id}.png")
        download_image(image_url, local_path)
        return local_path, image_url
    except Exception as e:
        logger.error(f"Error fetching asset image: {e}")
        raise HTTPException(status_code=500, detail="Failed to download asset image.")

@router.post("/get_asset_description")
async def get_asset_description(data: AssetData):
    """
    Endpoint to fetch the asset description using OpenAI and return the image URL.
    :param data: AssetData containing the asset_id.
    :return: JSON containing the generated asset description and image URL.
    """
    try:
        image_path, image_url = download_asset_image(data.asset_id)
        prompt = (
            "Please provide a detailed description of this Roblox asset image. "
            "Include details about its appearance, features, and any notable characteristics."
        )
        ai_description = generate_description_from_image(image_path, prompt)
        return {
            "description": ai_description,
            "imageUrl": image_url
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing asset description request: {e}")
        return {"error": f"Failed to process request: {str(e)}"}

@router.post("/get_player_description")
async def get_player_description(data: PlayerDescriptionRequest):
    """
    Endpoint to fetch the player's avatar description using OpenAI.
    :param data: PlayerDescriptionRequest containing the user_id.
    :return: JSON containing the generated description.
    """
    try:
        image_path = download_avatar_image(data.user_id)
        ai_description = generate_avatar_description_from_image(image_path)
        return {"description": ai_description}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing player description request: {e}")
        return {"error": f"Failed to process request: {str(e)}"}

def generate_description_from_image(image_path: str, prompt: str, max_length: int = 300) -> str:
    """
    Generate a description for an image using OpenAI's model.
    :param image_path: Path to the image.
    :param prompt: Prompt for the description.
    :param max_length: Maximum length of the generated description.
    :return: Generated description.
    """
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

@router.post("/robloxgpt/v3")
async def enhanced_chatgpt_endpoint_v3(request: Request):
    logger.info(f"Received request to /robloxgpt/v3 endpoint")

    try:
        data = await request.json()
        logger.debug(f"Request data: {data}")

        chat_message = EnhancedChatMessageV3(**data)
        logger.info(f"Validated enhanced chat message: {chat_message}")
    except Exception as e:
        logger.error(f"Failed to parse or validate data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    # Fetch the OpenAI API key from the environment
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found")
        raise HTTPException(status_code=500, detail="OpenAI API key not found")

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    conversation = conversation_manager.get_conversation(chat_message.player_id, chat_message.npc_id)
    logger.debug(f"Conversation history: {conversation}")

    try:
        context_summary = f"""
        NPC: {chat_message.npc_name}. 
        Player: {chat_message.context.get('player_name', 'Unknown')}. 
        New conversation: {chat_message.context.get('is_new_conversation', True)}. 
        Time since last interaction: {chat_message.context.get('time_since_last_interaction', 'N/A')}. 
        Nearby players: {', '.join(chat_message.context.get('nearby_players', []))}. 
        NPC location: {chat_message.context.get('npc_location', 'Unknown')}.
        """

        if chat_message.perception:
            context_summary += f"""
            Visible objects: {', '.join(chat_message.perception.visible_objects)}.
            Visible players: {', '.join(chat_message.perception.visible_players)}.
            Recent memories: {', '.join([str(m) for m in chat_message.perception.memory[-5:]])}.
            """

        logger.debug(f"Context summary: {context_summary}")

        system_prompt = f"{chat_message.system_prompt}\n\n{NPC_SYSTEM_PROMPT_ADDITION}\n\nContext: {context_summary}"

        messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": "assistant" if i % 2 else "user", "content": msg} for i, msg in enumerate(conversation)],
            {"role": "user", "content": chat_message.message}
        ]
        logger.debug(f"Messages to OpenAI: {messages}")

        logger.info(f"Sending request to OpenAI API for NPC: {chat_message.npc_name}")
        try:
            # Using beta.chat.completions.parse for structured output
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=chat_message.limit,
                response_format=NPCResponseV3
            )

            # Check if the model refused the request
            # Check the finish reason from the model's response
            if response.choices[0].finish_reason == "refusal":
                logger.error(f"Model refused to comply: {response.choices[0].message.content}")
                npc_response = NPCResponseV3(
                    message="I'm sorry, but I can't assist with that request.",
                    action=NPCAction(type="none")
                )
            else:
                # Parse the response content
                ai_message = response.choices[0].message.content  # Access the content attribute directly
                npc_response = NPCResponseV3(**json.loads(ai_message))
                logger.debug(f"Parsed NPC response: {npc_response}")
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            npc_response = NPCResponseV3(
                message="I'm sorry, I'm having trouble understanding right now.",
                action=NPCAction(type="none")
            )
        except Exception as e:
            logger.error(f"Error processing OpenAI API request: {e}", exc_info=True)
            npc_response = NPCResponseV3(
                message="I'm sorry, I'm having trouble understanding right now.",
                action=NPCAction(type="none")
            )

        conversation_manager.update_conversation(chat_message.player_id, chat_message.npc_id, chat_message.message)
        conversation_manager.update_conversation(chat_message.player_id, chat_message.npc_id, npc_response.message)

        return JSONResponse(npc_response.dict())

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@router.post("/robloxgpt/v3/heartbeat")
async def heartbeat_update(request: Request):
    try:
        data = await request.json()
        npc_id = data.get("npc_id")
        logs = data.get("logs", [])
        logger.info(f"Heartbeat received from NPC: {npc_id}")
        logger.debug(f"Logs received: {logs}")

        # Here you would typically store or process the logs
        return JSONResponse({"status": "acknowledged"})
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Updated endpoint for the dashboard
@router.get("/dashboard")
async def get_dashboard_data():
    try:
        # Read the AssetDatabase.json file using the imported function
        asset_data = load_json_database(JSON_DATABASE_PATH)

        # Extract the assets from the JSON data
        assets = [
            {
                "id": asset["assetId"],
                "name": asset["name"],
                "description": asset["description"],
                "image_url": asset["imageUrl"]
            }
            for asset in asset_data["assets"]
        ]

        # For now, we'll keep the NPCs and players as mock data
        npcs = [
            {"id": "1", "name": "Merchant", "description": "A friendly merchant"},
            {"id": "2", "name": "Guard", "description": "A vigilant guard"}
        ]
        players = [
            {"id": "1", "name": "Player1", "description": "An adventurous player"},
            {"id": "2", "name": "Player2", "description": "A skilled warrior"}
        ]

        return JSONResponse({"assets": assets, "npcs": npcs, "players": players})
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")

# New endpoint for adding assets
@router.post("/add_asset")
async def add_asset(asset: AssetData):
    try:
        # Get the asset description and image URL
        description_response = await get_asset_description(asset)
        
        # Read the current AssetDatabase.json
        asset_database = load_json_database(JSON_DATABASE_PATH)
        
        # Create the new asset entry
        new_asset = {
            "assetId": asset.asset_id,
            "name": asset.name,
            "description": description_response["description"],
            "imageUrl": description_response["imageUrl"]
        }
        
        # Add the new asset to the database
        asset_database["assets"].append(new_asset)
        
        # Write the updated database back to the JSON file
        save_json_database(JSON_DATABASE_PATH, asset_database)
        
        # Update the Lua database
        save_lua_database(LUA_DATABASE_PATH, asset_database)
        
        return JSONResponse(new_asset)
    except Exception as e:
        logger.error(f"Error adding new asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to add new asset")

# New endpoint to update asset descriptions
@router.post("/update_asset_descriptions")
async def update_asset_descriptions_endpoint(request: UpdateAssetsRequest):
    try:
        # Load the current asset database
        asset_db = load_json_database(JSON_DATABASE_PATH)

        # Update the asset descriptions
        updated_db = update_asset_descriptions(
            asset_db,
            overwrite=request.overwrite,
            single_asset=request.single_asset,
            only_empty=request.only_empty
        )

        # Save the updated database to JSON
        save_json_database(JSON_DATABASE_PATH, updated_db)

        # Save the updated database to Lua
        save_lua_database(LUA_DATABASE_PATH, updated_db)

        return JSONResponse({"message": "Asset descriptions updated successfully"})
    except Exception as e:
        logger.error(f"Error updating asset descriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to update asset descriptions")

# New endpoint for deleting items (assets, NPCs, players)
@router.delete("/delete_item/{item_type}/{item_id}")
async def delete_item(item_type: str, item_id: str):
    try:
        if item_type == "asset":
            # Load the current asset database
            asset_database = load_json_database(JSON_DATABASE_PATH)
            
            # Remove the asset with the given ID
            asset_database["assets"] = [asset for asset in asset_database["assets"] if asset["assetId"] != item_id]
            
            # Save the updated database to JSON
            save_json_database(JSON_DATABASE_PATH, asset_database)
            
            # Update the Lua database
            save_lua_database(LUA_DATABASE_PATH, asset_database)
        elif item_type in ["npc", "player"]:
            # Implement deletion for NPCs and players if needed
            pass
        else:
            raise HTTPException(status_code=400, detail="Invalid item type")

        return JSONResponse({"message": f"{item_type.capitalize()} with ID {item_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting {item_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete {item_type}")

# New endpoint for editing items (assets, NPCs, players)
@router.put("/edit_item/{item_type}/{item_id}")
async def edit_item(item_type: str, item_id: str, item: EditItemRequest):
    try:
        if item_type == "asset":
            # Load the current asset database
            asset_database = load_json_database(JSON_DATABASE_PATH)
            
            # Find and update the asset with the given ID
            for asset in asset_database["assets"]:
                if asset["assetId"] == item_id:
                    asset["description"] = item.description
                    break
            else:
                raise HTTPException(status_code=404, detail="Asset not found")
            
            # Save the updated database to JSON
            save_json_database(JSON_DATABASE_PATH, asset_database)
            
            # Update the Lua database
            save_lua_database(LUA_DATABASE_PATH, asset_database)
        elif item_type in ["npc", "player"]:
            # Implement editing for NPCs and players if needed
            pass
        else:
            raise HTTPException(status_code=400, detail="Invalid item type")

        return JSONResponse({"message": f"{item_type.capitalize()} with ID {item_id} updated successfully"})
    except Exception as e:
        logger.error(f"Error editing {item_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to edit {item_type}")
