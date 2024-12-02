from fastapi import APIRouter, HTTPException, Depends
from letta_roblox.client import LettaRobloxClient
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .database import get_npc_context, create_agent_mapping, get_agent_mapping
import logging

logger = logging.getLogger("roblox_app")

# Initialize router and client
router = APIRouter(prefix="/letta/v1", tags=["letta"])
letta_client = LettaRobloxClient("http://localhost:8283")

"""
Letta AI Integration Router

This module provides endpoints for integrating Letta AI agents with NPCs.
It handles:
- Agent creation and management
- Conversation persistence
- NPC context and memory management

Integration Flow:
1. When an NPC first interacts with a participant, a Letta agent is created
2. The agent is initialized with the NPC's context (personality, abilities, etc.)
3. The agent_mapping table maintains the relationship between NPCs and Letta agents
4. Subsequent interactions use the same agent to maintain conversation context

Example Usage:
    POST /letta/v1/chat
    {
        "npc_id": 123,
        "participant_id": "player_456",
        "message": "Hello!",
        "system_prompt": "Optional override for NPC's default prompt"
    }
"""

class ChatRequest(BaseModel):
    npc_id: int  # Changed to int to match database
    participant_id: str
    message: str
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_npc(request: ChatRequest):
    try:
        # First try to get existing agent mapping
        agent_mapping = get_agent_mapping(
            npc_id=request.npc_id,
            participant_id=request.participant_id
        )
        
        if not agent_mapping:
            # Get NPC context for new agent creation
            npc_context = get_npc_context(request.npc_id)
            if not npc_context:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Create new agent with rich context
            agent = letta_client.create_agent(
                npc_type="npc",
                initial_memory={
                    "human": f"Participant ID: {request.participant_id}",
                    "persona": npc_context["system_prompt"] or request.system_prompt or "I am an NPC in a virtual world.",
                    "description": npc_context["description"],
                    "abilities": npc_context["abilities"],
                    "display_name": npc_context["display_name"]
                }
            )
            
            # Store the mapping
            agent_mapping = create_agent_mapping(
                npc_id=request.npc_id,
                participant_id=request.participant_id,
                agent_id=agent["id"]
            )
            
            logger.info(f"Created new agent mapping: {agent_mapping.model_dump()}")
        
        # Send message to agent
        response = letta_client.send_message(
            agent_mapping.agent_id,
            request.message
        )
        
        # Format response
        return ChatResponse(
            message=response if isinstance(response, str) else response.get("message", ""),
            conversation_id=response.get("conversation_id") if isinstance(response, dict) else None,
            metadata=response.get("metadata") if isinstance(response, dict) else None,
            action=response.get("action") if isinstance(response, dict) else None
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{npc_id}/{participant_id}")
async def delete_agent(npc_id: int, participant_id: str):
    try:
        # Get the agent mapping
        agent_mapping = get_agent_mapping(npc_id, participant_id)
        if not agent_mapping:
            return {"status": "not_found", "message": "Agent not found"}
            
        # Delete agent from Letta
        letta_client.delete_agent(agent_mapping.agent_id)
        
        # Delete from database
        with get_db() as db:
            db.execute("""
                DELETE FROM agent_mappings 
                WHERE npc_id = ? AND participant_id = ?
            """, (npc_id, participant_id))
            db.commit()
            
        return {"status": "success", "message": "Agent deleted"}
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 