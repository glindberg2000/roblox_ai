# app/routers_v4.py

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import os

from .models import (
    EnhancedChatRequest, 
    ConversationResponse, 
    NPCResponseV3, 
    NPCAction
)
from .ai_handler import AIHandler
from .conversation_managerV2 import ConversationManagerV2
from .config import NPC_SYSTEM_PROMPT_ADDITION

# Initialize logging
logger = logging.getLogger("ella_app")

# Initialize router with v4 prefix
router = APIRouter(prefix="/v4")

# Initialize managers
conversation_manager = ConversationManagerV2()
ai_handler = AIHandler(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat")
async def enhanced_chat_endpoint(request: EnhancedChatRequest):
    """
    Enhanced chat endpoint supporting different conversation types
    and persistent conversation state
    """
    try:
        logger.info(f"V4 Chat request: {request.conversation_type} from {request.initiator_id}")

        # Validate conversation type
        if request.conversation_type not in ["npc_user", "npc_npc", "group"]:
            raise HTTPException(status_code=422, detail="Invalid conversation type")

        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create participants with appropriate types based on conversation_type
            initiator_data = {
                "id": request.initiator_id,
                "type": "npc" if request.conversation_type.startswith("npc") else "player",
                "name": request.context.get("initiator_name", f"Entity_{request.initiator_id}")
            }
            
            target_data = {
                "id": request.target_id,
                "type": "npc" if request.conversation_type.endswith("npc") else "player",
                "name": request.context.get("target_name", f"Entity_{request.target_id}")
            }
            
            # Create Participant objects before passing to create_conversation
            conversation_id = conversation_manager.create_conversation(
                type=request.conversation_type,
                participant1_data=initiator_data,
                participant2_data=target_data
            )
            
            if not conversation_id:
                raise HTTPException(
                    status_code=429,
                    detail="Cannot create new conversation - rate limit or participant limit reached"
                )

        # Get conversation history
        history = conversation_manager.get_history(conversation_id)
        
        # Prepare context for AI
        context_summary = f"""
        Conversation type: {request.conversation_type}
        Initiator: {request.context.get('initiator_name', request.initiator_id)}
        Target: {request.context.get('target_name', request.target_id)}
        """

        if request.context:
            context_details = "\n".join(f"{k}: {v}" for k, v in request.context.items() 
                                      if k not in ['initiator_name', 'target_name'])
            if context_details:
                context_summary += f"\nAdditional context:\n{context_details}"

        # Prepare messages for AI
        messages = [
            {"role": "system", "content": f"{request.system_prompt}\n\n{NPC_SYSTEM_PROMPT_ADDITION}\n\nContext: {context_summary}"},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg} 
              for i, msg in enumerate(history)],
            {"role": "user", "content": request.message}
        ]

        # Mock AI response for testing
        if os.getenv("TESTING"):
            response = NPCResponseV3(
                message="Test response",
                action=NPCAction(type="none")
            )
        else:
            response = await ai_handler.get_response(
                messages=messages,
                system_prompt=request.system_prompt
            )

        # Add messages to conversation history
        conversation_manager.add_message(
            conversation_id,
            request.initiator_id,
            request.message
        )
        
        if response.message:
            conversation_manager.add_message(
                conversation_id,
                request.target_id,
                response.message
            )

        # Check for conversation end
        if response.action and response.action.type == "stop_talking":
            conversation_manager.end_conversation(conversation_id)
            logger.info(f"Ending conversation {conversation_id} due to stop_talking action")

        # Get conversation metadata
        metadata = conversation_manager.get_conversation_context(conversation_id)

        return ConversationResponse(
            conversation_id=conversation_id,
            message=response.message,
            action=NPCAction(type=response.action.type, data=response.action.data or {}),
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Error in v4 chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def end_conversation_endpoint(conversation_id: str):
    """Manually end a conversation"""
    try:
        conversation_manager.end_conversation(conversation_id)
        return JSONResponse({"status": "success", "message": "Conversation ended"})
    except Exception as e:
        logger.error(f"Error ending conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{participant_id}")
async def get_participant_conversations(participant_id: str):
    """Get all active conversations for a participant"""
    try:
        conversations = conversation_manager.get_active_conversations(participant_id)
        return JSONResponse({
            "participant_id": participant_id,
            "conversations": [
                conversation_manager.get_conversation_context(conv_id)
                for conv_id in conversations
            ]
        })
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics():
    """Get conversation metrics"""
    return JSONResponse({
        "conversation_metrics": conversation_manager.metrics.dict()
    })