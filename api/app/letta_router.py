from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional, List, Tuple, Set
from pydantic import BaseModel, validator
from datetime import datetime
import logging
import json
import uuid
import time
import requests
import httpx
import inspect
from letta_client import Letta
import os

# Core agent and tools
from letta_templates.npc_tools import (
    create_personalized_agent_v3,
    create_letta_client,
    TOOL_INSTRUCTIONS,
    TOOL_REGISTRY,
    navigate_to,
    navigate_to_coordinates,
    perform_action,
    examine_object
)

# Memory management functions
from letta_templates.npc_utils_v2 import (
    update_status_block as letta_update_status,
    update_group_block as letta_update_group,
    get_memory_block,
    update_memory_block,
    get_location_history,
    get_group_history,
    extract_agent_response,
    upsert_group_member,
)

from letta_templates.npc_test_data import DEMO_BLOCKS

# Keep all local imports
from .database import (
    get_npc_context,
    create_agent_mapping,
    get_agent_mapping,
    get_db,
    get_player_info,
    get_location_coordinates,
    get_all_locations,
    create_agent_mapping_v3,
    get_agent_mapping_v3
)
from .cache import (
    NPC_CACHE,        # Contains all NPC info including descriptions
    PLAYER_CACHE,     # Contains all player info
    AGENT_ID_CACHE,   # Maps NPCs to agents
    get_npc_id_from_name,  # Cache lookup helpers
    get_agent_id,
    get_npc_description,
    LOCATION_CACHE    # Add this import
)
from .mock_player import MockPlayer
from .config import (
    DEFAULT_LLM, 
    LLM_CONFIGS, 
    EMBEDDING_CONFIGS, 
    DEFAULT_EMBEDDING
)
from .models import (
    GameSnapshot,
    ClusterData,
    HumanContextData,
    GroupUpdate
)
from .letta_utils import extract_tool_results, convert_tool_calls_to_action
from pathlib import Path
from .queue_system import queue_system, ChatQueueItem, SnapshotQueueItem
from .snapshot_processor import enrich_snapshot_with_context
from .main import LETTA_CONFIG
from .group_manager import GroupMembershipManager
from letta_templates.npc_prompts import PLAYER_JOIN_MESSAGE, PLAYER_LEAVE_MESSAGE
from .utils import get_current_action  # Import from utils instead
from .group_processor import GroupProcessor

# Convert config to LLMConfig objects
# LLM_CONFIGS = {
#     name: LLMConfig(**config) 
#     for name, config in LLM_CONFIGS.items()
# }
# 
# # Convert config to EmbeddingConfig objects
# EMBEDDING_CONFIGS = {
#     name: EmbeddingConfig(**config)
#     for name, config in EMBEDDING_CONFIGS.items()
# }

logger = logging.getLogger("roblox_app")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see all logs

# Add a debug message to verify level
logger.debug("=== LOGGER DEBUG TEST ===")

# Initialize router and client
router = APIRouter(prefix="/letta/v1", tags=["letta"])

# Initialize ONE client properly
direct_client = create_letta_client()

print("\nDEBUG - Message API Signature:")
print(inspect.signature(direct_client.agents.messages.create))

print("\nDEBUG - Group Update Function Signature:")
print(inspect.signature(letta_update_group))

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
    messages: List[Dict[str, str]]  # Array of {content, role, name}
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None

# Add new model for status updates
class StatusUpdateRequest(BaseModel):
    npc_id: str
    status_text: str  # Changed from separate fields to single status_text

class GroupUpdate(BaseModel):
    npc_id: str
    player_id: str  # Now expects string
    player_name: str
    is_joining: bool

    @validator('player_id')
    def validate_player_id(cls, v):
        try:
            id_num = int(v)
            if id_num <= 0:
                raise ValueError()
            return v
        except:
            raise ValueError(f"Invalid Roblox UserId format: {v}")

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
                llm_config=LLM_CONFIGS[DEFAULT_LLM],
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
            logger.info(f"Chat using agent {agent_mapping.letta_agent_id} for NPC {request.npc_id}")
            logger.info(f"  This agent is in cache: {agent_mapping.letta_agent_id in AGENT_ID_CACHE.values()}")
        
        # Send message to agent
        logger.info(f"Sending message to agent {agent_mapping.letta_agent_id}")
        try:
            # Get name from context
            speaker_name = request.context.get("participant_name")
            logger.info(f"Message details:")
            logger.info(f"  agent_id: {agent_mapping.letta_agent_id}")
            logger.info(f"  role: {message_role}")
            logger.info(f"  message: {request.message}")
            logger.info(f"  speaker_name: {speaker_name}")
            
            response = direct_client.send_message(
                agent_id=agent_mapping.letta_agent_id,
                role=message_role,
                message=request.message,
                name=speaker_name
            )
            
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response content: {response}")
            
        except Exception as e:
            logger.error(f"Error sending message to Letta: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {e.__dict__}")
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
    try:
        logger.info(f"Processing chat request for NPC {request.npc_id}")
        logger.info(f"Processing chat request with context: {request.context}")
        
        # Determine message role
        message_role = "system" if request.message.startswith("[SYSTEM]") else "user"
        logger.info(f"Determined message role: {message_role} for message: {request.message[:50]}...")
        
        # Get or create agent mapping
        mapping = get_agent_mapping(
            request.npc_id,
            request.participant_id
        )
        
        if not mapping:
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
            memory = create_agent_memory(direct_client, npc_details, human_description)
            logger.info(f"Using memory for agent creation: {memory}")
            
            system_prompt = gpt_system.get_system_text("memgpt_chat").strip()

            agent = create_roblox_agent(
                client=direct_client,
                name=f"npc_{npc_details['display_name']}_{request.npc_id[:8]}_{request.participant_id[:8]}_{str(uuid.uuid4())[:8]}",
                memory=memory,
                system=system_prompt,
                llm_type=request.context.get("llm_type", DEFAULT_LLM)
            )
            
            # Store mapping
            mapping = create_agent_mapping(
                npc_id=request.npc_id,
                participant_id=request.participant_id,
                agent_id=agent.id
            )
            print(f"Created new agent mapping: {mapping}")
        else:
            print(f"Using existing agent {mapping.letta_agent_id} for {request.participant_id}")
        
        # Send message to agent
        logger.info(f"Sending message to agent {mapping.letta_agent_id}")
        try:
            # Get name from context
            speaker_name = request.context.get("participant_name")
            logger.info(f"Message details:")
            logger.info(f"  agent_id: {mapping.letta_agent_id}")
            logger.info(f"  role: {message_role}")
            logger.info(f"  message: {request.message}")
            logger.info(f"  speaker_name: {speaker_name}")
            
            # Send message using new API format
            letta_request = {
                "agent_id": mapping.letta_agent_id,
                "messages": [{
                    "content": request.message,
                    "role": message_role,
                    "name": speaker_name
                }]
            }
            
            response = direct_client.agents.messages.create(**letta_request)
            
            # Use our existing response handling
            result = extract_agent_response(response)
            logger.debug("=== Letta Response ===")
            logger.debug(f"Message: {result['message']}")
            logger.debug(f"Tool calls: {result['tool_calls']}")
            
            # Handle None message during tool calls
            if result['message'] is None and result['tool_calls']:
                logger.info("Got None message during tool call, waiting for completion")
                return ChatResponse(
                    message="",  # Empty string instead of None
                    action=convert_tool_calls_to_action(result["tool_calls"]),
                    metadata={
                        "tool_calls": result["tool_calls"],
                        "reasoning": result.get("reasoning", "")
                    }
                )
            
            # Convert tool calls to action
            action = convert_tool_calls_to_action(result["tool_calls"])
            logger.debug(f"Converted action: {action}")
            
            return ChatResponse(
                message=result["message"],
                action=action,  # Now using our converted action
                metadata={
                    "tool_calls": result["tool_calls"],
                    "reasoning": result.get("reasoning", "")
                }
            )

        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
            return ChatResponse(
                message="Something went wrong!",
                action={"type": "none"},
                metadata={"error": str(e)}
            )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return ChatResponse(
            message="Something went wrong!",
            action={"type": "none"},
            metadata={"error": str(e)}
        )

# Tool registration function
def register_base_tools(client) -> List[str]:
    """Register base tools for all agents and return tool IDs"""
    # Get existing tools
    existing_tools = {tool.name: tool.id for tool in client.list_tools()}
    logger.info(f"Found existing tools: {existing_tools}")
    
    tool_ids = []
    for name, info in TOOL_REGISTRY.items():
        if name in existing_tools:
            logger.info(f"Tool already exists: {name} (ID: {existing_tools[name]})")
            tool_ids.append(existing_tools[name])
        else:
            logger.info(f"Registering new tool: {name}")
            tool = client.create_tool(info["function"], name=name)
            tool_ids.append(tool.id)
            logger.info(f"Registered tool: {name} (ID: {tool.id})")
    
    return tool_ids

def extract_tool_results(response):
    """Extract tool results using SDK message types"""
    results = {
        'tool_calls': [],
        'reasoning': None,
        'final_message': None
    }
    
    if hasattr(response, 'messages'):
        current_tool = None
        
        for msg in response.messages:
            # Handle Tool Calls
            if isinstance(msg, ToolCallMessage):
                try:
                    # Parse the arguments JSON string
                    arguments = json.loads(msg.tool_call.arguments)
                    
                    current_tool = {
                        'name': msg.tool_call.name,
                        'arguments': arguments,  # Store parsed JSON
                        'status': None,
                        'result': None
                    }
                    results['tool_calls'].append(current_tool)
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse tool arguments: {msg.tool_call.arguments}")
                    
            # Handle Tool Returns
            elif isinstance(msg, ToolReturnMessage):
                if current_tool:
                    current_tool.update({
                        'status': msg.status,
                        'result': msg.tool_return
                    })
            
            # Handle Reasoning
            elif isinstance(msg, ReasoningMessage):
                results['reasoning'] = msg.reasoning

    return results

def create_agent_for_npc(npc_context: dict, participant_id: str):
    """Create agent with navigation tools and location memory"""
    
    # 1. Create memory blocks
    memory = {
        "persona": {
            "name": npc_context["displayName"],
            "description": npc_context["systemPrompt"]
        },
        "human": {
            "name": participant_id,  # Player's name/ID
            "description": "A Roblox player exploring the game"
        },
        "locations": {
            "known_locations": [
                # Slug-based location
                {
                    "name": "Pete's Stand",
                    "description": "A friendly food stand run by Pete",
                    "coordinates": [-12.0, 18.9, -127.0],
                    "slug": "petes_stand"
                },
                # Coordinate-based locations
                {
                    "name": "Secret Garden",
                    "description": "A hidden garden with rare flowers",
                    "coordinates": [15.5, 20.0, -110.8]
                    # No slug - will use coordinates
                },
                {
                    "name": "Town Square",
                    "description": "Central gathering place with fountain",
                    "coordinates": [45.2, 12.0, -89.5],
                    "slug": "town_square"  # Optional with coordinates
                },
                {
                    "name": "Market District",
                    "description": "Busy shopping area with many vendors",
                    "coordinates": [-28.4, 15.0, -95.2],
                    "slug": "market_district"
                }
            ]
        }
    }

    # 2. Only register the tools we need
    tools_to_register = {
        "navigate_to": TOOL_REGISTRY["navigate_to"],  # Updated tool name
        "perform_action": TOOL_REGISTRY["perform_action"]
    }

    # 3. Create agent with tools and memory
    agent = direct_client.create_agent(
        name=f"{npc_context['displayName']}_{participant_id}",
        system=npc_context["systemPrompt"] + TOOL_INSTRUCTIONS,
        memory=memory,
        embedding_config=embedding_config,
        llm_config=llm_config,
        include_base_tools=True
    )

    # 4. Register only navigation tools
    for name, info in tools_to_register.items():
        tool = direct_client.create_tool(info["function"], name=name)
        logger.info(f"Created tool: {name} for navigation")

    return agent

def process_tool_results(tool_results: dict) -> Tuple[str, dict]:
    """Process tool results and extract message/action"""
    message = None
    action = {"type": "none"}

    try:
        for tool_call in tool_results.get("tool_calls", []):
            logger.info(f"Processing tool call: {tool_call}")
            
            if tool_call["name"] == "perform_action":
                args = tool_call["arguments"]
                
                # Handle different action types
                if args.get("action") == "follow":
                    action = {
                        "type": "follow",
                        "data": {
                            "target": args.get("target")
                        }
                    }
                    message = "I'll follow you!"
                    
                elif args.get("action") == "unfollow":
                    action = {
                        "type": "unfollow",
                        "data": {}
                    }
                    message = "I'll stop following!"
                    
                elif args.get("action") == "emote":
                    action = {
                        "type": "emote",
                        "data": {
                            "emote_type": args.get("type"),
                            "target": args.get("target")
                        }
                    }
                    message = f"*{args.get('type')}s*"
                    
            elif tool_call["name"] == "navigate_to":
                result = json.loads(tool_call["result"])
                logger.info(f"Parsed navigation result: {result}")
                
                if result["status"] == "success":
                    # Try to get coordinates from database
                    logger.info(f"Looking up coordinates for slug: {result['slug']}")
                    coordinates = get_location_coordinates(result["slug"])
                    
                    if coordinates:
                        logger.info(f"Found coordinates in database: {coordinates}")
                        action = {
                            "type": "navigate",
                            "data": {
                                "coordinates": coordinates
                            }
                        }
                    else:
                        logger.warning(f"No coordinates found for slug {result['slug']}, using fallback")
                        action = {
                            "type": "navigate",
                            "data": {
                                "coordinates": {
                                    "x": 100,
                                    "y": 0,
                                    "z": 100
                                }
                            }
                        }
                    message = result.get("message", "Moving to new location...")
                    logger.info(f"Navigation action created: {action}")
                    
            elif tool_call["name"] == "send_message":
                message = tool_call["arguments"].get("message", "...")
                
    except Exception as e:
        logger.error(f"Error processing tool results: {str(e)}", exc_info=True)
        message = "I'm having trouble right now."
        action = {"type": "none"}

    return message, action

def get_coordinates_for_slug(slug: str) -> Optional[Dict]:
    """Look up coordinates directly from database - synchronous version"""
    try:
        with get_db() as db:
            location = db.execute(
                "SELECT coordinates FROM locations WHERE slug = ? AND game_id = ?",
                (slug, 61)
            ).fetchone()
            
            if location and location['coordinates']:
                coords = json.loads(location['coordinates'])
                logger.info(f"Found coordinates for slug {slug}: {coords}")
                return coords
                
        logger.warning(f"No location data found for slug: {slug}")
        return None
            
    except Exception as e:
        logger.error(f"Error getting coordinates for slug {slug}: {e}")
        return None

def create_memory_blocks(npc_details: dict) -> dict:
    """Create standardized memory blocks for NPC"""
    return {
        "locations": {
            "known_locations": [
                {
                    "name": data['name'],
                    "slug": slug,
                    "coordinates": data['coordinates']
                }
                for slug, data in LOCATION_CACHE.items()
            ],
            "visited_locations": [],
            "favorite_spots": []
        },
        "status": "Ready to interact with visitors",
        "group_members": {
            "players": {}
        },
        "persona": f"""I am {npc_details.get('name', npc_details.get('display_name'))}.
{npc_details.get('system_prompt', '')}""",
        "journal": "[]"
    }

@router.post("/snapshot/game")
async def process_game_snapshot(snapshot: GameSnapshot):
    try:
        logger.info("=== Processing New Game Snapshot ===")
        logger.debug(f"Raw snapshot data: {json.dumps(snapshot.dict(), indent=2)}")
        
        # Use our tested enrichment logic
        enriched_snapshot = enrich_snapshot_with_context(snapshot)
        logger.info("Snapshot enriched with context")
        
        group_manager = GroupMembershipManager()
        logger.info(f"Group Manager State - Pending Removals: {group_manager.pending_removals}")
        
        # Process each entity
        for entity_id, context in enriched_snapshot.humanContext.items():
            if entity_id not in NPC_CACHE:
                continue
                
            logger.info(f"\n=== Processing NPC: {entity_id} ===")
            
            # Handle group join/leave messages first
            # ... (keep existing group message logic) ...
            
            # Use our tested status block update
            logger.info("Processing status updates...")
            await process_npc_status(entity_id, context, enriched_snapshot)
            
        logger.info("=== Snapshot Processing Complete ===")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing snapshot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/v3")
async def chat_with_npc_v3(request: ChatRequest):
    try:
        logger.info(f"Processing chat request for NPC {request.npc_id}")
        
        # Add detailed message sequence logging
        logger.info("=== Message Sequence Start ===")
        for i, msg in enumerate(request.messages):
            logger.info(f"Message {i}:")
            logger.info(f"  Role: {msg.get('role')}")
            logger.info(f"  Content: {msg.get('content')}")
            logger.info(f"  Context: {msg.get('context')}")
            logger.info(f"  Name: {msg.get('name')}")
            logger.info(f"  Is System Message: {msg.get('role') == 'system'}")
            logger.info(f"  Is Assistant Message: {msg.get('role') == 'assistant'}")
            logger.info(f"  Is User Message: {msg.get('role') == 'user'}")
        logger.info("=== Message Sequence End ===")

        # Continue with normal processing - no blocking
        agent_id = get_agent_id(request.npc_id)
        
        if not agent_id:
            # Only create new agent if not in cache
            logger.info(f"No cached agent for NPC {request.npc_id} - creating new one")
            
            # Get NPC details
            npc_details = get_npc_context(request.npc_id)
            
            # Create new agent
            blocks = create_memory_blocks(npc_details)
            agent = create_personalized_agent_v3(
                name=npc_details['display_name'],
                memory_blocks=blocks,
                llm_type="openai",
                with_custom_tools=True,
                prompt_version="FULL"
            )

            # Create mapping and update cache
            mapping = create_agent_mapping_v3(request.npc_id, agent.id)
            AGENT_ID_CACHE[request.npc_id] = agent.id
            logger.info(f"Created new agent {agent.id} and updated cache")
            agent_id = agent.id
        else:
            logger.info(f"Using cached agent {agent_id} for NPC {request.npc_id}")

        # Send message using cached agent_id
        logger.info(f"Sending message to agent {agent_id}")
        try:
            # Send message using new API format
            letta_request = {
                "agent_id": agent_id,
                "messages": request.messages
            }
            
            # Log what we're sending to Letta
            logger.info("=== Sending to Letta ===")
            logger.info(f"Agent ID: {agent_id}")
            logger.info(f"Request: {json.dumps(letta_request, indent=2)}")
            
            response = direct_client.agents.messages.create(**letta_request)
            
            # Log raw response from Letta - but handle datetime objects
            logger.info("=== Raw Letta Response ===")
            logger.info(f"Response Type: {type(response)}")
            logger.info(f"Response Content: {str(response)}")  # Use str() instead of json.dumps
            
            # Log what we extract
            result = extract_agent_response(response)
            logger.info("=== Extracted Response ===")
            logger.info(f"Message: {result.get('message')}")
            logger.info(f"Tool Calls: {result.get('tool_calls')}")
            logger.info(f"Reasoning: {result.get('reasoning')}")
            
            # If system message about proximity and no response, add default greeting
            if (any(msg.get('role') == 'system' and 'has entered your range' in msg.get('content', '') 
                    for msg in request.messages) and not result.get('message')):
                logger.info("Adding default greeting for proximity message")
                result['message'] = "Hi there! Default greeting!"
            
            # Handle None message during tool calls
            if result['message'] is None and result['tool_calls']:
                logger.info("Got None message during tool call, waiting for completion")
                return ChatResponse(
                    message="",  # Empty string instead of None
                    action=convert_tool_calls_to_action(result["tool_calls"]),
                    metadata={
                        "tool_calls": result["tool_calls"],
                        "reasoning": result.get("reasoning", "")
                    }
                )
            
            # Convert tool calls to proper Roblox action format
            action = convert_tool_calls_to_action(result["tool_calls"])
            logger.debug(f"Converted action: {action}")
            
            # Log what we send back
            logger.info("=== Sending to Client ===")
            response = ChatResponse(
                message=result["message"],
                action=action,  # Now using our converted action
                metadata={
                    "tool_calls": result["tool_calls"],
                    "reasoning": result.get("reasoning", "")
                }
            )
            logger.info(f"Final Response: {json.dumps(response.dict(), indent=2)}")
            
            return response

        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
            return ChatResponse(
                message="Something went wrong!",
                action={"type": "none"},
                metadata={"error": str(e)}
            )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return ChatResponse(
            message="Something went wrong!",
            action={"type": "none"},
            metadata={"error": str(e)}
        )

async def process_snapshot_groups(human_context):
    """Process group updates from snapshot data using LettaDev patterns"""
    try:
        logger.info("🔍 === SNAPSHOT DEBUG START ===")  # Use emoji for visibility
        
        # Test log at different levels
        logger.debug("🔍 DEBUG TEST")
        logger.info("🔍 INFO TEST")
        logger.warning("🔍 WARNING TEST")
        logger.error("🔍 ERROR TEST")
        
        for entity_name, context in human_context.items():
            logger.info(f"🔍 Entity: {entity_name}")  # Use INFO instead of DEBUG
            logger.info(f"🔍 Raw context: {context}")
            logger.info(f"🔍 Has position: {hasattr(context, 'position')}")
            
            if hasattr(context, 'position'):
                logger.info(f"🔍 Position values: x={getattr(context.position, 'x', None)}, "
                          f"y={getattr(context.position, 'y', None)}, "
                          f"z={getattr(context.position, 'z', None)}")

        # Group NPCs by their current group members
        cluster_groups = {}
        
        for entity_name, context in human_context.items():
            position = getattr(context, "position", None)
            
            # Get narrative location if we have position
            location = "Unknown"
            if position:
                location = position.get_location_narrative()  # Use narrative instead of coordinates
                logger.debug(f"[Position] Formatted location for {entity_name}: {location}")
            
            # Debug group formation
            group_key = tuple(sorted(context.currentGroups.members))
            logger.debug(f"\nProcessing group for {entity_name}")
            logger.debug(f"Group key: {group_key}")
            
            if group_key not in cluster_groups:
                cluster_groups[group_key] = {
                    'members': set(context.currentGroups.members),
                    'agent_ids': [],
                    'locations': {}
                }
                logger.debug(f"Created new cluster group: {cluster_groups[group_key]}")
            
            # Store location
            cluster_groups[group_key]['locations'][entity_name] = location
            logger.debug(f"Stored location for {entity_name}: {location}")
            
            # Get agent info
            npc_id = get_npc_id_from_name(entity_name)
            if npc_id:
                agent_id = get_agent_id(npc_id)
                if agent_id:
                    cluster_groups[group_key]['agent_ids'].append(agent_id)
                    logger.debug(f"Added agent {agent_id} for {entity_name}")
                    
                    # Debug current memory state
                    status = get_memory_block(direct_client, agent_id, "status")
                    logger.debug(f"\nCurrent status for {entity_name} ({agent_id}):")
                    logger.debug(json.dumps(status, indent=2))

        # Process clusters
        logger.debug("\n=== PROCESSING CLUSTERS ===")
        for members_key, data in cluster_groups.items():
            logger.debug(f"\nCluster members: {members_key}")
            logger.debug(f"Locations: {data['locations']}")
            logger.debug(f"Agent IDs: {data['agent_ids']}")
            
            nearby_players = [
                {
                    "id": member,
                    "name": member,
                    "appearance": get_npc_description(member) or '',
                    "notes": ''
                }
                for member in data['members']
            ]
            
            for agent_id in data['agent_ids']:
                try:
                    member_name = next(name for name in data['members'] 
                                    if get_agent_id(get_npc_id_from_name(name)) == agent_id)
                    location = data['locations'].get(member_name, "Unknown")
                    
                    # Update location with new function
                    status = update_location_status(
                        client=direct_client,
                        agent_id=agent_id,
                        current_location=location,
                        current_action="idle"
                    )
                    
                    # Update group with new function
                    group = update_group_members_v2(
                        client=direct_client,
                        agent_id=agent_id,
                        members=[{
                            "id": p["id"],
                            "name": p["name"],
                            "location": p.get("location", "Unknown"),
                            "appearance": p.get("appearance", "")
                        } for p in nearby_players]
                    )
                    
                    # Get histories for logging
                    location_history = get_location_history(direct_client, agent_id)
                    group_history = get_group_history(direct_client, agent_id)
                    logger.debug(f"Location history: {json.dumps(location_history, indent=2)}")
                    logger.debug(f"Group history: {json.dumps(group_history, indent=2)}")
                    
                except Exception as e:
                    logger.error(f"Failed to update agent {agent_id}: {str(e)}")
                    continue
        
        logger.debug("=== SNAPSHOT DEBUG END ===")
            
    except Exception as e:
        logger.error(f"Error in process_snapshot_groups: {str(e)}")
        raise

def verify_group_state(client, agent_ids: List[str], snapshot_data: Dict[str, Any]):
    """Debug helper to check group state consistency"""
    logger.info("\nSnapshot vs Memory State Check:")
    
    # 1. Print snapshot state
    logger.info(f"\nSnapshot shows cluster:")
    logger.info(json.dumps(snapshot_data, indent=2))
    
    # 2. Check each agent's memory
    for agent_id in agent_ids:
        try:
            group_block = get_memory_block(client, agent_id, "group_members")
            logger.info(f"\nAgent {agent_id} memory shows:")
            logger.info(json.dumps(group_block, indent=2))
            
            # Highlight inconsistencies
            memory_members = set(group_block.get("members", {}).keys())
            snapshot_members = set(snapshot_data.get("cluster_members", []))
            
            if memory_members != snapshot_members:
                logger.warning("\nMismatch detected!")
                logger.warning(f"Missing in memory: {snapshot_members - memory_members}")
                logger.warning(f"Extra in memory: {memory_members - snapshot_members}")
        except Exception as e:
            logger.error(f"Error checking agent {agent_id}: {str(e)}")

def run_group_health_check(client, members: Tuple[str, ...]) -> bool:
    """Regular health check for group state"""
    try:
        # Get agent IDs for members
        agent_ids = []
        for member in members:
            npc_id = get_npc_id_from_name(member)
            if npc_id:
                agent_id = get_agent_id(npc_id)
                if agent_id:
                    agent_ids.append(agent_id)
        
        if not agent_ids:
            logger.warning("No agent IDs found for health check")
            return False
            
        # Compare group states
        states: Dict[str, Set[str]] = {}
        for agent_id in agent_ids:
            try:
                group = get_memory_block(client, agent_id, "group_members")
                if group and "members" in group:
                    states[agent_id] = set(group["members"].keys())
            except Exception as e:
                logger.error(f"Error getting state for {agent_id}: {str(e)}")
                continue
        
        if not states:
            logger.warning("No states found to compare")
            return False
            
        # Find inconsistencies
        reference_state = next(iter(states.values()))
        mismatched = {
            agent_id: members 
            for agent_id, members in states.items() 
            if members != reference_state
        }
        
        if mismatched:
            logger.warning("Found state mismatches:")
            for agent_id, members in mismatched.items():
                logger.warning(f"Agent {agent_id}: {members}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

@router.post("/chat/v4")
async def chat_with_npc_v4(request: ChatRequest):
    """Queue chat requests and return ticket"""
    try:
        ticket = str(uuid.uuid4())
        logger.info(f"[CHAT_V4] Creating ticket: {ticket}")
        
        # Create queue item
        queue_item = ChatQueueItem(
            npc_id=request.npc_id,
            message=request.message,
            timestamp=time.time(),
            context=request.dict(),
            cluster_id=None  # Optional: Add cluster tracking later
        )
        
        # Add to queue
        await queue_system.enqueue_chat(queue_item)
        logger.info(f"[CHAT_V4] Queued message with ticket: {ticket}")
        
        return {
            "status": "queued",
            "ticket": ticket
        }
    except Exception as e:
        logger.error(f"[CHAT_V4] Queue error: {str(e)}")
        raise

@router.get("/v4/queue")
async def get_queue_status():
    """Get current queue status"""
    try:
        status = queue_system.get_queue_sizes()
        
        # Get last 3 snapshots safely
        snapshot_queue = queue_system.snapshot_queue._queue
        last_snapshots = []
        for i in range(max(0, len(snapshot_queue)-3), len(snapshot_queue)):
            if i < len(snapshot_queue):
                item = snapshot_queue[i]
                last_snapshots.append({
                    "cluster_count": len(item.clusters),
                    "entities": sum(len(c.members) for c in item.clusters),
                    "age": f"{time.time() - item.timestamp:.1f}s ago"
                })
        
        summary = {
            "overview": {
                "chats_queued": status["total_chats"],
                "snapshots_queued": status["total_snapshots"],
                "snapshot_rate": f"{status['current_snapshot_rate']}/sec",
                "queue_age": f"{status['queue_age_seconds']:.1f} seconds",
                "processing_status": "Active" if status["current_snapshot_rate"] > 0 else "Idle"
            },
            "chat_queue": [
                {
                    "npc": item.npc_id.split('-')[0],
                    "message": item.message[:50] + "..." if len(item.message) > 50 else item.message,
                    "age": f"{time.time() - item.timestamp:.1f}s ago",
                    "context": {
                        "cluster_id": item.cluster_id,
                        "participant": item.context.get("participant_id", "unknown")
                    }
                }
                for item in queue_system.chat_queue._queue
            ],
            "snapshot_queue": {
                "total": len(snapshot_queue),
                "last_snapshots": last_snapshots,
                "processing_rate": f"{status['current_snapshot_rate']:.1f} snapshots/sec"
            }
        }
        
        logger.info(f"[QUEUE] Status: {json.dumps(summary['overview'], indent=2)}")
        logger.info(f"[QUEUE] Active chats: {len(summary['chat_queue'])}")
        logger.info(f"[QUEUE] Recent snapshots: {json.dumps(summary['snapshot_queue']['last_snapshots'], indent=2)}")
        
        return summary
    except Exception as e:
        logger.error(f"[CHAT_V4] Queue status error: {str(e)}")
        raise

async def process_npc_status(entity_id: str, context: HumanContextData, enriched_snapshot: GameSnapshot):
    try:
        agent_id = get_agent_id(get_npc_id_from_name(entity_id))
        if not agent_id:
            logger.warning(f"No agent ID found for NPC {entity_id} - skipping status update")
            return
            
        # Update status if needed
        if hasattr(context, 'needs_status_update') and context.needs_status_update:
            # Get current location and action
            current_location = context.location if hasattr(context, 'location') else "Unknown"
            current_action = get_current_action(context)
            
            # Log the status update trigger
            logger.info(f"Status update needed for {entity_id}")
            logger.info(f"  Location: {current_location}")
            logger.info(f"  Action: {current_action}")
            
            status_text = f"Location: {current_location} | Action: {current_action}"
            logger.info(f"Updating status for {entity_id}: {status_text}")
            letta_update_status(direct_client, agent_id, status_text, send_notification=False)
        
        # Only update group if members changed
        if context.currentGroups and context.currentGroups.members:
            # Get current group data
            current_group = get_memory_block(direct_client, agent_id, "group_members")
            current_members = set(current_group.get("members", {}).keys()) if current_group else set()
            new_members = set(context.currentGroups.members)
            
            if current_members != new_members:
                logger.info(f"Group members changed for {entity_id}")
                logger.info(f"  Old members: {current_members}")
                logger.info(f"  New members: {new_members}")
                
                group_data = {
                    "members": {},
                    "summary": f"Current members: {', '.join(new_members)}",
                    "updates": []
                }
                
                for member in new_members:
                    appearance = get_npc_description(member)
                    group_data["members"][member] = {
                        "name": member,
                        "appearance": appearance or '',
                        "last_seen": datetime.now().isoformat(),
                        "notes": ""
                    }
                
                letta_update_group(direct_client, agent_id, group_data, send_notification=False)

    except Exception as e:
        logger.error(f"Error updating status block: {e}", exc_info=True)

def get_current_action(context: HumanContextData) -> str:
    """Determine current action from context"""
    if context.health and context.health.get('state') == 'Dead':
        return "Dead"
    elif context.health and context.health.get('current') < context.health.get('max', 100) * 0.3:
        return "Severely injured"
    elif context.health and context.health.get('current') < context.health.get('max', 100) * 0.7:
        return "Injured"
    elif context.health and context.health.get('isMoving'):
        return "Moving"
    return "Idle"  # Default action

@router.post("/npc/group/update")
async def update_group(update: GroupUpdate):
    """Update NPC group membership when players join/leave"""
    try:
        agent_id = get_agent_id(update.npc_id)
        if not agent_id:
            raise HTTPException(status_code=404, detail="No agent found for NPC")
            
        # Get player info from cache/db
        player_info = PLAYER_CACHE.get(update.player_id) or {}
        
        # Use upsert_group_member
        result = upsert_group_member(
            client=direct_client,
            agent_id=agent_id,
            entity_id=str(update.player_id),
            update_data={
                "name": update.player_name,
                "is_present": update.is_joining,
                "health": "healthy",
                "appearance": player_info.get("description", "Unknown"),
                "last_seen": datetime.now().isoformat()
            }
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "updated": datetime.now().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error updating group: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/npc/status/update")
async def update_npc_status(request: StatusUpdateRequest):
    """Update NPC's status block with current state"""
    try:
        agent_id = get_agent_id(request.npc_id)
        if not agent_id:
            logger.error(f"No agent found for NPC {request.npc_id}")
            raise HTTPException(status_code=404, detail="No agent found for NPC")
            
        # Parse status text into components
        # Example input: "health: 100 | current_action: Idle | location: plaza"
        status_parts = dict(part.strip().split(": ") for part in request.status_text.split("|"))
        
        # Build status block with first-person description
        status_block = {
            "current_location": status_parts.get("location", "unknown"),
            "state": status_parts.get("current_action", "Idle"),
            "description": generate_status_description(
                location=status_parts.get("location"),
                action=status_parts.get("current_action"),
                health=status_parts.get("health")
            )
        }
        
        # Update using new format
        letta_update_status(
            client=direct_client,
            agent_id=agent_id,
            field_updates=status_block
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "status": {
                "text": request.status_text,
                "last_updated": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating NPC status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update status: {str(e)}"
        )

def generate_status_description(location: str = None, action: str = None, health: str = None) -> str:
    """Generate first-person status description"""
    if not location:
        return "I'm wandering around..."
        
    templates = {
        "Idle": "I'm standing at {location}, taking in the surroundings",
        "Moving": "I'm walking towards {location}",
        "Interacting": "I'm chatting with visitors at {location}",
        "Injured": "I'm at {location}, nursing my wounds",
        "Dead": "I've fallen at {location}"
    }
    
    template = templates.get(action, templates["Idle"])
    return template.format(location=location)

