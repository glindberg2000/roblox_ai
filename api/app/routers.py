from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
import json
import logging
from app.conversation_manager import ConversationManager
from openai import OpenAI
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("ella_app")

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
    limit: int = 200

class NPCAction(BaseModel):
    type: Literal["follow", "unfollow", "none"]
    data: Optional[Dict[str, Any]] = None

class NPCResponseV3(BaseModel):
    message: str
    action: Optional[NPCAction] = None
    internal_state: Optional[Dict[str, Any]] = None

NPC_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "action": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["follow", "unfollow", "none"]
                }
            },
            "required": ["type"],
            "additionalProperties": False
        },
        "internal_state": {"type": "object"}
    },
    "required": ["message", "action"],
    "additionalProperties": False
}

conversation_manager = ConversationManager()

# V3 Endpoint Implementation
@router.post("/robloxgpt/v3")
async def enhanced_chatgpt_endpoint_v3(request: Request):
    logger.info(f"Received request to /robloxgpt/v3 endpoint")
    
    try:
        # Log the raw request data
        data = await request.json()
        logger.debug(f"Request data: {data}")
        
        # Create the EnhancedChatMessageV3 model
        chat_message = EnhancedChatMessageV3(**data)
        logger.info(f"Validated enhanced chat message: {chat_message}")
    except Exception as e:
        logger.error(f"Failed to parse or validate data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found")
        raise HTTPException(status_code=500, detail="OpenAI API key not found")

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Get the conversation history for the NPC and player
    conversation = conversation_manager.get_conversation(chat_message.player_id, chat_message.npc_id)
    logger.debug(f"Conversation history: {conversation}")

    try:
        # Build the context summary
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

        # Build the messages for the API call
        messages = [
            {"role": "system", "content": f"{chat_message.system_prompt}\n\nContext: {context_summary}"},
            *[{"role": "assistant" if i % 2 else "user", "content": msg} for i, msg in enumerate(conversation)],
            {"role": "user", "content": chat_message.message}
        ]
        logger.debug(f"Messages to OpenAI: {messages}")

        # Make the API call to OpenAI
        logger.info(f"Sending request to OpenAI API for NPC: {chat_message.npc_name}")
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            max_tokens=chat_message.limit,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "npc_response",
                    "strict": True,
                    "schema": NPC_RESPONSE_SCHEMA
                }
            }
        )
        
        ai_message = response.choices[0].message.content
        logger.debug(f"AI response: {ai_message}")

        # Parse the structured output
        try:
            structured_response = json.loads(ai_message)
            npc_response = NPCResponseV3(**structured_response)
            logger.debug(f"Parsed NPC response: {npc_response}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            npc_response = NPCResponseV3(message="I'm sorry, I'm having trouble understanding right now.")

        # Update the conversation history
        conversation_manager.update_conversation(chat_message.player_id, chat_message.npc_id, chat_message.message)
        conversation_manager.update_conversation(chat_message.player_id, chat_message.npc_id, npc_response.message)

        return JSONResponse(npc_response.dict())

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@router.post("/robloxgpt/v3/heartbeat")
async def heartbeat_update(request: Request):
    try:
        # Log the received request
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