from fastapi import APIRouter, HTTPException, Depends, Request
from letta import ChatMemory, LLMConfig
from letta_roblox.client import LettaRobloxClient
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .database import get_npc_context, create_agent_mapping, get_agent_mapping, get_db
from .mock_player import MockPlayer
import logging

logger = logging.getLogger("roblox_app")

# Initialize router and client
router = APIRouter(prefix="/letta/v1", tags=["letta"])
letta_client = LettaRobloxClient("http://localhost:8333")

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
    logger.info(f"Received request from game: {request.model_dump_json()}")
    try:
        # Get NPC context
        npc_context = get_npc_context(request.npc_id)
        logger.info(f"Got NPC context: {npc_context}")
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
            
            # Create memory using proper class
            memory = ChatMemory(
                human=f"""You are talking to {request_context.get('participant_name', 'a player')}.
                        Description: {get_player_description(request.participant_id)}""".strip(),
                persona=npc_details['system_prompt']
            )
            
            # Create new agent with proper config
            agent = letta_client.create_agent(
                name=f"npc_{npc_details['display_name']}",
                memory=memory,
                llm_config=LLMConfig(
                    model="gpt-4o-mini",
                    model_endpoint_type="openai",
                    model_endpoint="https://api.openai.com/v1",
                    context_window=128000
                ),
                system=npc_details['system_prompt'],
                include_base_tools=True
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
        logger.info(f"Sending message to agent {agent_mapping['letta_agent_id']}")
        try:
            response = letta_client.send_message(
                agent_mapping["letta_agent_id"],
                request.message
            )
            logger.info(f"Got response from Letta: {response}")
        except Exception as e:
            logger.error(f"Error sending message to Letta: {str(e)}")
            raise
        
        # Format response
        return ChatResponse(
            message=response if isinstance(response, str) else response.get("message", ""),
            conversation_id=response.get("conversation_id") if isinstance(response, dict) else None,
            metadata={
                **(response.get("metadata", {}) if isinstance(response, dict) else {}),
                "participant_type": request_context.get("participant_type", "player"),
                "interaction_id": request_context.get("interaction_id"),
                "is_npc_chat": request_context.get("participant_type") == "npc"
            },
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

def create_mock_participant(npc_context: Dict) -> MockPlayer:
    """Create a mock participant for NPC-NPC interactions"""
    return MockPlayer(
        display_name=npc_context["display_name"],
        npc_id=npc_context["id"]
    )

@router.post("/npc-chat", response_model=ChatResponse)
async def npc_to_npc_chat(
    npc_id: str,
    target_npc_id: str,
    message: str
):
    """Handle NPC to NPC chat"""
    try:
        # Get both NPCs' context
        npc1_context = get_npc_context(npc_id)
        npc2_context = get_npc_context(target_npc_id)
        
        if not npc1_context or not npc2_context:
            raise HTTPException(status_code=404, detail="NPC not found")
            
        # Create mock participants
        npc1_participant = create_mock_participant(npc1_context)
        npc2_participant = create_mock_participant(npc2_context)
        
        # Get or create agent mappings
        npc1_agent = get_or_create_agent_mapping(npc_id, f"npc_{target_npc_id}")
        npc2_agent = get_or_create_agent_mapping(target_npc_id, f"npc_{npc_id}")
        
        # Send message from NPC1 to NPC2
        response = letta_client.send_message(
            npc2_agent["letta_agent_id"],
            message
        )
        
        return ChatResponse(
            message=response.get("message", ""),
            conversation_id=response.get("conversation_id"),
            metadata=response.get("metadata"),
            action=response.get("action")
        )
    except Exception as e:
        logger.error(f"Error in NPC-NPC chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add to router startup
@router.on_event("startup")
async def startup_event():
    pass 

def get_player_description(participant_id: str) -> str:
    """Get stored player description from database"""
    with get_db() as db:
        result = db.execute(
            "SELECT description FROM player_descriptions WHERE player_id = ?",
            (participant_id,)
        ).fetchone()
        return result['description'] if result else ""