from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
import logging
from app.conversation_manager import ConversationManager
from openai import OpenAI, OpenAIError
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
from app.config import NPC_SYSTEM_PROMPT_ADDITION
import json

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
    type: Literal["follow", "unfollow", "stop_talking", "none"]
    data: Optional[Dict[str, Any]] = None

class NPCResponseV3(BaseModel):
    message: str
    action: NPCAction
    internal_state: Optional[Dict[str, Any]] = None

conversation_manager = ConversationManager()

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
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
                max_tokens=chat_message.limit,
                response_format=NPCResponseV3
            )

            # Check if the model refused the request
            # Check the finish reason from the model's response
            if response.choices[0].finish_reason == "refusal":
                logger.error(f"Model refused to comply: {response.choices[0].message['content']}")
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