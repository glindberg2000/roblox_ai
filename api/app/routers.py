import os
import logging
import json
from typing import Literal, Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAI, OpenAIError
from app.conversation_manager import ConversationManager
from app.config import (
    NPC_SYSTEM_PROMPT_ADDITION,
    STORAGE_DIR, 
    ASSETS_DIR, 
    THUMBNAILS_DIR, 
    AVATARS_DIR
)
from .utils import (
    load_json_database, 
    save_json_database, 
    save_lua_database, 
    get_database_paths
)
from .image_utils import (
    download_avatar_image,
    download_asset_image,
    generate_image_description,
    get_asset_description
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get database paths
DB_PATHS = get_database_paths()

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


# def generate_avatar_description_from_image(image_path: str, max_length: int = 300) -> str:
#     base64_image = encode_image(image_path)
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": (
#                                 f"Please provide a detailed description of this Roblox avatar within {max_length} characters. "
#                                 "Include details about the avatar's clothing, accessories, colors, any unique features, and its overall style or theme."
#                             ),
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{base64_image}"
#                             },
#                         }
#                     ],
#                 }
#             ]
#         )
#         description = response.choices[0].message.content
#         return description
#     except OpenAIError as e:
#         logger.error(f"OpenAI API error: {e}")
#         return "No description available."

# def download_avatar_image(user_id: str) -> str:
#     avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
#     try:
#         response = requests.get(avatar_api_url)
#         response.raise_for_status()
#         image_url = response.json()['data'][0]['imageUrl']
#         return download_image(image_url, os.path.join(AVATAR_SAVE_PATH, f"{user_id}.png"))
#     except Exception as e:
#         logger.error(f"Error fetching avatar image: {e}")
#         raise HTTPException(status_code=500, detail="Failed to download avatar image.")

# def download_asset_image(asset_id: str) -> tuple[str, str]:
#     asset_api_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
#     try:
#         response = requests.get(asset_api_url)
#         response.raise_for_status()
#         image_url = response.json()['data'][0]['imageUrl']
#         local_path = os.path.join(ASSET_IMAGE_SAVE_PATH, f"{asset_id}.png")
#         download_image(image_url, local_path)
#         return local_path, image_url
#     except Exception as e:
#         logger.error(f"Error fetching asset image: {e}")
#         raise HTTPException(status_code=500, detail="Failed to download asset image.")

# def generate_description_from_image(image_path: str, prompt: str, max_length: int = 300) -> str:
#     base64_image = encode_image(image_path)
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": f"{prompt} Limit the description to {max_length} characters."
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{base64_image}"
#                             },
#                         }
#                     ],
#                 }
#             ]
#         )
#         description = response.choices[0].message.content
#         return description
#     except OpenAIError as e:
#         logger.error(f"OpenAI API error: {e}")
#         return "No description available."

# @router.post("/get_asset_description")
# async def get_asset_description(data: AssetData):
#     try:
#         image_path, image_url = download_asset_image(data.asset_id)
#         prompt = (
#             "Please provide a detailed description of this Roblox asset image. "
#             "Include details about its appearance, features, and any notable characteristics."
#         )
#         ai_description = generate_description_from_image(image_path, prompt)
#         return {
#             "description": ai_description,
#             "imageUrl": image_url
#         }
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Error processing asset description request: {e}")
#         return {"error": f"Failed to process request: {str(e)}"}

# @router.post("/get_player_description")
# async def get_player_description(data: PlayerDescriptionRequest):
#     try:
#         image_path = download_avatar_image(data.user_id)
#         ai_description = generate_avatar_description_from_image(image_path)
#         return {"description": ai_description}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Error processing player description request: {e}")
#         return {"error": f"Failed to process request: {str(e)}"}


@router.post("/get_asset_description")
async def get_asset_description_endpoint(data: AssetData):
    """Endpoint to get asset description using AI."""
    try:
        result = await get_asset_description(data.asset_id, data.name)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing asset description request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get_player_description")
async def get_player_description_endpoint(data: PlayerDescriptionRequest):
    """Endpoint to get player avatar description using AI."""
    try:
        # Download image and get its path
        image_path = await download_avatar_image(data.user_id)
        
        # Generate description using the generic description function
        prompt = (
            "Please provide a detailed description of this Roblox avatar. "
            "Include details about the avatar's clothing, accessories, colors, "
            "unique features, and overall style or theme."
        )
        description = await generate_image_description(image_path, prompt)
        
        return {"description": description}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing player description request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

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
            if response.choices[0].finish_reason == "refusal":
                logger.error(f"Model refused to comply: {response.choices[0].message.content}")
                npc_response = NPCResponseV3(
                    message="I'm sorry, but I can't assist with that request.",
                    action=NPCAction(type="none")
                )
            else:
                # Parse the response content
                ai_message = response.choices[0].message.content
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

        return JSONResponse({"status": "acknowledged"})
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=400, detail=str(e))
