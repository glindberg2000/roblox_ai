from fastapi import APIRouter, HTTPException, Depends, Request
from letta import ChatMemory, LLMConfig, EmbeddingConfig, create_client
from letta.prompts import gpt_system
from letta_roblox.client import LettaRobloxClient
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .database import get_npc_context, create_agent_mapping, get_agent_mapping, get_db, get_player_info
from .mock_player import MockPlayer
from .config import DEFAULT_LLM, LLM_CONFIGS, EMBEDDING_CONFIGS, DEFAULT_EMBEDDING
import logging
import json
import uuid
import time

# Convert config to LLMConfig objects
LLM_CONFIGS = {
    name: LLMConfig(**config) 
    for name, config in LLM_CONFIGS.items()
}

# Convert config to EmbeddingConfig objects
EMBEDDING_CONFIGS = {
    name: EmbeddingConfig(**config)
    for name, config in EMBEDDING_CONFIGS.items()
}

def create_roblox_agent(
    client, 
    name: str,
    memory: ChatMemory,
    system: str,
    embedding_config: Optional[EmbeddingConfig] = None,
    llm_type: str = None
):
    """Create a Letta agent configured for Roblox NPCs"""
    # Use config default if no llm_type specified
    llm_type = llm_type or DEFAULT_LLM
    llm_config = LLM_CONFIGS.get(llm_type, LLM_CONFIGS[DEFAULT_LLM])
    
    # Use provided embedding config or default from config
    embedding_config = embedding_config or EMBEDDING_CONFIGS[DEFAULT_EMBEDDING]
    
    return client.create_agent(
        name=name,
        embedding_config=embedding_config,
        llm_config=llm_config,
        memory=memory,
        system=system,
        include_base_tools=True,
        description="A Roblox NPC"
    )

logger = logging.getLogger("roblox_app")

# Initialize router and client
router = APIRouter(prefix="/letta/v1", tags=["letta"])
letta_client = LettaRobloxClient("http://localhost:8283")

# Initialize direct SDK client (keeping old client for backwards compatibility)
direct_client = create_client(base_url="http://localhost:8283")

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
            
            # Add participant type handling
            participant_type = request.context.get("participant_type", "player")
            participant_info = None
            
            if participant_type == "npc":
                participant_info = get_npc_context(request.participant_id)
                if participant_info:  # Only use NPC context if found
                    human_description = f"""This is what I know about the NPC:
Name: {participant_info['display_name']}
Description: {participant_info['system_prompt']}"""
                else:
                    # Fallback to player lookup if NPC not found
                    participant_type = "player"
            
            # Handle player case (either direct or fallback)
            if participant_type == "player":
                player_info = get_player_info(request.participant_id)
                human_description = f"""This is what I know about the player:
Name: {player_info['display_name'] or request_context.get('participant_name', 'a player')}
Description: {player_info['description']}"""
            
            # Create memory using the appropriate description
            memory = ChatMemory(
                human=human_description.strip(),
                persona=f"""My name is {npc_details['display_name']}.
{npc_details['system_prompt']}""".strip()
            )
            
            # Create new agent with proper config
            agent = letta_client.create_agent(
                name=f"npc_{npc_details['display_name']}_{request.npc_id[:8]}_{request.participant_id[:8]}_{str(uuid.uuid4())[:8]}",
                memory=memory,
                llm_config=LLMConfig(
                    model="gpt-4o-mini",
                    model_endpoint_type="openai",
                    model_endpoint="https://api.openai.com/v1",
                    context_window=128000
                ),
                system=gpt_system.get_system_text("memgpt_chat"),
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
            print(f"Using existing agent {agent_mapping.letta_agent_id} for {request.participant_id}")
        
        # Send message to agent
        logger.info(f"Sending message to agent {agent_mapping.letta_agent_id}")
        try:
            logger.info(f"Using direct_client: {direct_client}")
            logger.info(f"Agent ID: {agent_mapping.letta_agent_id}")
            logger.info(f"Message: {request.message}")
            response = direct_client.send_message(
                agent_id=agent_mapping.letta_agent_id,
                role="user",
                message=request.message
            )
            logger.info(f"Got response from Letta: {response}")
        except Exception as e:
            logger.error(f"Error sending message to Letta: {str(e)}", exc_info=True)
            raise
        
        # Extract message from function call
        message = None
        for msg in response.messages:
            if msg.message_type == "function_call":
                try:
                    args = json.loads(msg.function_call.arguments)
                    if "message" in args:
                        message = args["message"]
                        break
                except:
                    continue

        # Format response
        return ChatResponse(
            message=message or "I'm having trouble responding right now.",
            conversation_id=None,
            metadata={
                "participant_type": request_context.get("participant_type", "player"),
                "interaction_id": request_context.get("interaction_id"),
                "is_npc_chat": request_context.get("participant_type") == "npc"
            },
            action={"type": "none"}
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

@router.post("/chat/v2", response_model=ChatResponse)
async def chat_with_npc_v2(request: ChatRequest):
    """New endpoint using direct Letta SDK"""
    # Basic request logging
    logger.info(f"Received request from game: {request.model_dump_json()}")

    try:
        # Get NPC context
        npc_details = get_npc_context(request.npc_id)
        if not npc_details:
            raise HTTPException(status_code=404, detail="NPC not found")

        # Initialize context if None
        request_context = request.context or {}
        
        # Determine message role
        message_role = "user"  # Always treat incoming messages as user messages
        logger.info(f"Message role: {message_role} for {request.participant_id} -> {request.npc_id}")
        
        # Get existing agent mapping with strict ordering
        agent_mapping = get_agent_mapping(
            npc_id=request.npc_id,
            participant_id=request.participant_id,
            strict_order=True  # Ensure we get the right direction
        )
        
        if not agent_mapping:
            # Get NPC details for memory
            npc_details = get_npc_context(request.npc_id)
            
            # Add participant type handling
            participant_type = request.context.get("participant_type", "player")
            participant_info = None
            
            if participant_type == "npc":
                participant_info = get_npc_context(request.participant_id)
                if participant_info:  # Only use NPC context if found
                    human_description = f"""This is what I know about the NPC:
Name: {participant_info['display_name']}
Description: {participant_info['system_prompt']}"""
                else:
                    # Fallback to player lookup if NPC not found
                    participant_type = "player"
            
            # Handle player case (either direct or fallback)
            if participant_type == "player":
                player_info = get_player_info(request.participant_id)
                human_description = f"""This is what I know about the player:
Name: {player_info['display_name'] or request_context.get('participant_name', 'a player')}
Description: {player_info['description']}"""
            
            # Create memory using the appropriate description
            memory = ChatMemory(
                human=human_description.strip(),
                persona=f"""My name is {npc_details['display_name']}.
{npc_details['system_prompt']}""".strip()
            )
            
            # Create agent using new structure from quickstart
            agent = create_roblox_agent(
                client=direct_client,
                name=f"npc_{npc_details['display_name']}_{request.npc_id[:8]}_{request.participant_id[:8]}_{str(uuid.uuid4())[:8]}",
                memory=memory,
                system=gpt_system.get_system_text("memgpt_chat"),
                llm_type=request.context.get("llm_type", "claude")
            )
            
            # Store mapping
            agent_mapping = create_agent_mapping(
                npc_id=request.npc_id,
                participant_id=request.participant_id,
                agent_id=agent.id  # Note: agent.id instead of agent["id"]
            )
            print(f"Created new agent mapping: {agent_mapping}")
        else:
            print(f"Using existing agent {agent_mapping.letta_agent_id} for {request.participant_id}")
        
        # Send message to agent
        logger.info(f"Sending message to agent {agent_mapping.letta_agent_id}")
        try:
            response = direct_client.send_message(
                agent_id=agent_mapping.letta_agent_id,
                role=message_role,
                message=request.message
            )
            logger.info(f"Got response from Letta: {response}")
        except Exception as e:
            logger.error(f"Error sending message to Letta: {str(e)}")
            raise
        
        # Extract message from function call
        message = None
        for msg in response.messages:
            if msg.message_type == "function_call":
                try:
                    args = json.loads(msg.function_call.arguments)
                    if "message" in args:
                        message = args["message"]
                        break
                except:
                    continue

        # Format response
        return ChatResponse(
            message=message or "I'm having trouble responding right now.",
            conversation_id=None,
            metadata={
                "participant_type": request_context.get("participant_type", "player"),
                "interaction_id": request_context.get("interaction_id"),
                "is_npc_chat": request_context.get("participant_type") == "npc"
            },
            action={"type": "none"}
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

