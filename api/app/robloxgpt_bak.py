import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
import logging
from openai import OpenAI
from typing import Literal, Optional, Dict, Any, Union, List
from datetime import datetime, timedelta

logger = logging.getLogger("ella_app")
logger.setLevel(logging.DEBUG)

router = APIRouter()

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
    limit: int = 200  # Default limit of characters

class NPCAction(BaseModel):
    type: Literal["follow", "unfollow", "none"]
    data: Optional[Dict[str, Any]] = None  # Since follow/unfollow have no associated data

class NPCResponseV3(BaseModel):
    message: str
    action: Optional[NPCAction] = None
    internal_state: Optional[Dict[str, Any]] = None

# JSON Schema for Structured Output
# Revised JSON Schema for Structured Output
# Simplified JSON Schema for Structured Output (no emote)
NPC_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "action": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["follow", "unfollow", "none"]  # Only follow, unfollow, and none actions
                }
            },
            "required": ["type"],  # Only 'type' is required
            "additionalProperties": False  # No additional properties allowed
        },
        "internal_state": {"type": "object"}  # Internal state remains as a generic object
    },
    "required": ["message", "action"],  # Message and action are required
    "additionalProperties": False  # No additional properties allowed in the top-level object
}


class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.expiry_time = timedelta(minutes=30)

    def get_conversation(self, player_id, npc_id):
        key = (player_id, npc_id)
        if key in self.conversations:
            conversation, last_update = self.conversations[key]
            if datetime.now() - last_update > self.expiry_time:
                del self.conversations[key]
                return []
            return conversation
        return []

    def update_conversation(self, player_id, npc_id, message):
        key = (player_id, npc_id)
        if key not in self.conversations:
            self.conversations[key] = ([], datetime.now())
        conversation, _ = self.conversations[key]
        conversation.append(message)
        self.conversations[key] = (conversation[-50:], datetime.now())  # Keep last 50 messages

conversation_manager = ConversationManager()

# V3 Endpoint Implementation
@router.post("/robloxgpt/v3")
async def enhanced_chatgpt_endpoint_v3(request: Request):
    logger.info(f"Received request to /robloxgpt/v3 endpoint")
    
    try:
        data = await request.json()
        logger.debug(f"Parsed request data: {data}")
        
        chat_message = EnhancedChatMessageV3(**data)
        logger.info(f"Validated enhanced chat message: {chat_message}")
    except Exception as e:
        logger.error(f"Failed to parse or validate data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found")
        raise HTTPException(status_code=500, detail="OpenAI API key not found")

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Get conversation history
    conversation = conversation_manager.get_conversation(chat_message.player_id, chat_message.npc_id)
    
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
        
        logger.info(f"Context summary: {context_summary}")


        messages = [
            {"role": "system", "content": f"{chat_message.system_prompt}\n\nContext: {context_summary}"},
            *[{"role": "assistant" if i % 2 else "user", "content": msg} for i, msg in enumerate(conversation)],
            {"role": "user", "content": chat_message.message}
        ]

        logger.info(f"Sending request to OpenAI API for {chat_message.npc_name}")
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            max_tokens=chat_message.limit,
            response_format={
                "type": "json_schema",  # Use the structured output format
                "json_schema": {
                    "name": "npc_response",
                    "strict": True,
                    "schema": NPC_RESPONSE_SCHEMA
                }
            }
        )
        
        ai_message = response.choices[0].message.content
        logger.info(f"AI response for {chat_message.npc_name}: {ai_message}")

        # Parse the structured output
        try:
            structured_response = json.loads(ai_message)
            npc_response = NPCResponseV3(**structured_response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {ai_message}")
            npc_response = NPCResponseV3(message="I'm sorry, I'm having trouble understanding right now.")

        # Update conversation history
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
        logger.info(f"Logs received: {logs}")
        # Here you would typically store or process the logs
        return JSONResponse({"status": "acknowledged"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))