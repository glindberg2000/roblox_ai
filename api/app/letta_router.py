from fastapi import APIRouter, HTTPException, Depends, Request
from letta_roblox.client import LettaRobloxClient
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .database import get_npc_context, create_agent_mapping, get_agent_mapping, get_db
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
    npc_id: str  # Using UUID string from database
    participant_id: str
    message: str
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None

@router.post("/chat/debug", status_code=200)
async def debug_chat_request(request: Request):
    """Debug endpoint to see raw request data"""
    body = await request.json()
    print("Debug - Raw request body:", body)
    return {
        "received": body,
        "validation_model": ChatRequest.model_json_schema()
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_with_npc(request: ChatRequest):
    print("Received request:", request.model_dump_json())
    try:
        # Get NPC context
        npc_context = get_npc_context(request.npc_id)
        if not npc_context:
            raise HTTPException(status_code=404, detail="NPC not found")

        # Initialize context if None
        request_context = request.context or {}
        
        # Get existing agent mapping
        agent_mapping = get_agent_mapping(request.npc_id, request.participant_id)
        print(f"Found agent mapping: {agent_mapping}")

        if not agent_mapping:
            # Get NPC details for memory
            npc_details = get_npc_context(request.npc_id)
            
            # Create new agent with full memory
            agent = letta_client.create_agent(
                npc_type="npc",
                initial_memory={
                    "persona": f"""You are {npc_details['display_name']}.
                               Role: {npc_details['system_prompt']}
                               Abilities: {', '.join(npc_details.get('abilities', []))}
                               Description: {npc_details.get('description', '')}""".strip(),
                    "human": f"""You are talking to {request_context.get('participant_name', 'a player')}.
                            Player Description: {request_context.get('player_description', '')}""".strip()
                }
            )
            
            # Store new agent mapping
            agent_mapping = create_agent_mapping(
                npc_id=request.npc_id,
                participant_id=request.participant_id,
                agent_id=agent["id"]
            )
            print(f"Created new agent mapping: {agent_mapping}")
        else:
            print(f"Using existing agent {agent_mapping['letta_agent_id']} for {request.participant_id}")
        
        # Send message to agent
        response = letta_client.send_message(
            agent_mapping["letta_agent_id"],
            request.message
        )
        
        print(f"Got response from Letta: {response}")
        
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

# Add to router startup
@router.on_event("startup")
async def startup_event():
    pass 