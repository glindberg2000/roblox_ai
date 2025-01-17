from fastapi import APIRouter, HTTPException, Depends, Request
from letta import (
    ChatMemory, 
    LLMConfig, 
    EmbeddingConfig, 
    create_client,
    BasicBlockMemory
)
from datetime import datetime
from letta.prompts import gpt_system
from letta_roblox.client import LettaRobloxClient
from typing import Dict, Any, Optional, List, Tuple, Set
from pydantic import BaseModel
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
    HumanContextData
)
import logging
import json
import uuid
import time
from .letta_utils import extract_tool_results
from pathlib import Path
from letta.schemas.message import (
    ToolCallMessage, 
    ToolReturnMessage, 
    ReasoningMessage, 
    Message
)
from letta_templates.npc_tools import (
    TOOL_INSTRUCTIONS,  # Use official instructions
    TOOL_REGISTRY,
    navigate_to,
    navigate_to_coordinates,
    perform_action,
    examine_object
)
import requests
import httpx
from letta_templates import (
    create_personalized_agent,
    chat_with_agent,
    update_group_status
)
from .cache import get_npc_id_from_name, get_npc_description, get_agent_id  # Add import
from letta_templates.npc_utils import (
    get_memory_block,
    update_memory_block,
    update_group_status  # Add this!
)
from letta_templates import print_agent_details
from .queue_system import queue_system, ChatQueueItem, SnapshotQueueItem

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

def create_roblox_agent(
    client, 
    name: str,
    memory: ChatMemory,
    system: str,
    embedding_config: Optional[EmbeddingConfig] = None,
    llm_type: str = None,
    tools_section: str = TOOL_INSTRUCTIONS
):
    """Create a Letta agent configured for Roblox NPCs"""
    # Debug logging
    logger.info(f"Creating agent with llm_type: {llm_type}")
    logger.info(f"Default LLM from config: {DEFAULT_LLM}")
    
    # Use config default if no llm_type specified
    llm_type = llm_type or DEFAULT_LLM
    logger.info(f"Final llm_type selected: {llm_type}")
    
    # Get the config dictionary
    llm_config_dict = LLM_CONFIGS[llm_type]
    logger.info(f"Using LLM config: {llm_config_dict}")
    
    # Create LLMConfig object once
    llm_config = LLMConfig(**llm_config_dict)
    
    # Add debug logging to see the final config object
    logger.info(f"Created LLMConfig object: {llm_config}")
    logger.info(f"LLMConfig model_endpoint: {llm_config.model_endpoint}")
    
    # Use provided embedding config or default from config
    if not embedding_config:
        embedding_config = EmbeddingConfig(**EMBEDDING_CONFIGS[DEFAULT_EMBEDDING])
    
    # Start with the provided system prompt
    system_prompt = system

    # Add our tools section
    system_prompt = system_prompt.replace(
        "Base instructions finished.",
        TOOL_INSTRUCTIONS + "\nBase instructions finished."
    )

    logger.info(f"Created system prompt with tools section")

    # Get tool IDs
    tool_ids = register_base_tools(client)
    
    return client.create_agent(
        name=name,
        embedding_config=embedding_config,
        llm_config=llm_config,
        memory=memory,
        system=system_prompt,
        include_base_tools=True,
        tool_ids=tool_ids,
        description="A Roblox NPC"
    )

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
            
            response = direct_client.send_message(
                agent_id=mapping.letta_agent_id,
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
        
        # Extract tool results
        results = extract_tool_results(response)
        logger.info("Successfully extracted tool results")
        
        # Use process_tool_results instead of inline processing
        message, action = process_tool_results(results)
        
        # Return simplified response
        logger.info(f"Sending response - Message: {message}, Action: {action}")
        return ChatResponse(
            message=message,
            action=action,
            metadata={
                "debug": "Simplified response for testing"
            }
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

def create_agent_memory(
    direct_client: Any,
    npc_details: Dict,
    human_description: str
) -> BasicBlockMemory:
    """Create agent memory blocks including locations per LettaDev spec"""
    # Get locations from database
    known_locations = get_all_locations()
    
    # Simplify to just names and slugs
    simplified_locations = [
        {
            "name": loc["name"],
            "slug": loc["slug"]
        } for loc in known_locations
    ]
    
    logger.info(f"Loading {len(simplified_locations)} locations into agent memory")
    logger.info(f"Simplified location data: {json.dumps(simplified_locations, indent=2)}")
    
    # Create memory blocks
    persona_block = direct_client.create_block(
        label="persona",
        value=f"""My name is {npc_details['display_name']}.
{npc_details['system_prompt']}""".strip(),
        limit=2000
    )
    logger.info(f"Created persona block: {persona_block}")
    
    human_block = direct_client.create_block(
        label="human",
        value=human_description.strip(),
        limit=2000
    )
    logger.info(f"Created human block: {human_block}")
    
    locations_block = direct_client.create_block(
        label="locations",
        value=json.dumps({
            "known_locations": simplified_locations
        }),
        limit=5000
    )
    logger.info(f"Created locations block: {locations_block}")
    
    memory = BasicBlockMemory(blocks=[persona_block, human_block, locations_block])
    logger.info(f"Created memory with blocks: {memory}")
    
    return memory

@router.post("/snapshot/game")
async def process_game_snapshot(snapshot: GameSnapshot):
    try:
        # Log the incoming snapshot
        logger.info("Received game snapshot")
        logger.info(f"Processing {len(snapshot.clusters)} clusters")
        
        # Create and enqueue the snapshot
        snapshot_item = SnapshotQueueItem(
            clusters=snapshot.clusters,
            human_context=snapshot.humanContext,
            timestamp=time.time()
        )
        await queue_system.enqueue_snapshot(snapshot_item)
        
        # Process entities...

        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing game snapshot: {str(e)}")
        raise

@router.post("/chat/v3", response_model=ChatResponse)
async def chat_with_npc_v3(request: ChatRequest):
    try:
        logger.info(f"Processing chat request for NPC {request.npc_id}")
        logger.info(f"Processing chat request with context: {request.context}")
        
        # Determine message role
        message_role = "system" if request.message.startswith("[SYSTEM]") else "user"
        logger.info(f"Determined message role: {message_role} for message: {request.message[:50]}...")
        
        # Get or create agent mapping (using v3 functions)
        mapping = get_agent_mapping_v3(request.npc_id)
        
        if not mapping:
            # Get NPC details
            npc_details = get_npc_context(request.npc_id)
            
            # Create agent with required memory blocks
            agent = create_personalized_agent(
                name=npc_details['display_name'],  # Just use NPC name
                client=direct_client,
                minimal_prompt=True,
                memory_blocks={
                    # Keep existing memory blocks structure
                    "persona": {
                        "name": npc_details['display_name'],
                        "personality": npc_details.get('system_prompt', ''),
                        "interests": [],
                        "journal": []
                    },
                    "status": {
                        "current_location": request.context.get('npc_location', 'Unknown'),
                        "current_action": f"Just spawned at {datetime.now().isoformat()}",
                        "movement_state": "stationary"
                    },
                    "group_members": {
                        "members": {},
                        "summary": "No players nearby",
                        "updates": [],
                        "last_updated": datetime.now().isoformat()
                    },
                    "locations": {
                        "known_locations": [
                            {
                                "name": loc["name"],
                                "coordinates": loc["coordinates"],
                                "slug": loc["slug"]
                            }
                            for loc in get_all_locations()
                        ]
                    }
                }
            )

            # Create mapping using v3 function
            mapping = create_agent_mapping_v3(
                npc_id=request.npc_id,
                agent_id=agent.id
            )
        else:
            print(f"Using existing agent {mapping.letta_agent_id} for {request.participant_id}")

        # Send message to agent (using existing v2 code)
        logger.info(f"Sending message to agent {mapping.letta_agent_id}")
        try:
            # Get name from context
            speaker_name = request.context.get("participant_name")
            logger.info(f"Message details:")
            logger.info(f"  agent_id: {mapping.letta_agent_id}")
            logger.info(f"  role: {message_role}")
            logger.info(f"  message: {request.message}")
            logger.info(f"  speaker_name: {speaker_name}")
            
            response = direct_client.send_message(
                agent_id=mapping.letta_agent_id,
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
        
        # Extract tool results (using existing v2 code)
        results = extract_tool_results(response)
        logger.info("Successfully extracted tool results")
        
        # Use process_tool_results instead of inline processing
        message, action = process_tool_results(results)
        
        # Return simplified response
        logger.info(f"Sending response - Message: {message}, Action: {action}")
        return ChatResponse(
            message=message,
            action=action,
            metadata={
                "debug": "Simplified response for testing"
            }
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
                    
                    logger.debug(f"\nUpdating agent {agent_id} ({member_name})")
                    logger.debug(f"Location to set: {location}")
                    
                    # Get pre-update state
                    pre_status = get_memory_block(direct_client, agent_id, "status")
                    logger.debug(f"Pre-update status: {json.dumps(pre_status, indent=2)}")
                    
                    update_group_status(
                        client=direct_client,
                        agent_id=agent_id,
                        nearby_players=nearby_players,
                        current_location=location,  # This will now be the narrative
                        current_action="idle"
                    )
                    
                    # Verify update
                    post_status = get_memory_block(direct_client, agent_id, "status")
                    logger.debug(f"Post-update status: {json.dumps(post_status, indent=2)}")
                    
                    logger.info(f"Updated group status for agent {agent_id} at {location}")
                    
                except Exception as e:
                    logger.error(f"Failed to update agent {agent_id}: {str(e)}")
                    continue
        
        logger.debug("=== SNAPSHOT DEBUG END ===")
            
    except Exception as e:
        logger.error(f"Error in process_snapshot_groups: {str(e)}")
        raise

def update_group_status(client, agent_id: str, nearby_players: list, 
                       current_location: str, current_action: str = "idle"):
    """Update group and status blocks together"""
    try:
        # Get current blocks
        status = get_memory_block(client, agent_id, "status")
        group = get_memory_block(client, agent_id, "group_members")
        
        # Track group changes
        current_members = set(group.get("members", {}).keys())
        new_members = set(p["id"] for p in nearby_players)
        
        # Calculate who joined and left
        joined = new_members - current_members
        left = current_members - new_members
        
        updates = []
        if joined:
            joined_names = [p["name"] for p in nearby_players if p["id"] in joined]
            updates.append(f"{', '.join(joined_names)} joined the group")
        if left:
            left_names = [group["members"][pid]["name"] for pid in left]
            updates.append(f"{', '.join(left_names)} left the group")
        
        # Update status (preserve existing fields including coordinates)
        existing_status = status.copy()  # Make a copy
        existing_status.update({
            "current_location": current_location,
            "previous_location": status.get("current_location"),
            "current_action": current_action,
            "movement_state": "stationary" if current_action == "idle" else "moving"
        })
        status = existing_status  # Use updated copy
        
        # Update group (simplified structure)
        members = {}
        for player in nearby_players:
            members[player.get("id")] = {
                "name": player["name"],
                "appearance": player.get("appearance", ""),
                "notes": player.get("notes", "")
            }
        
        # Keep last 10 group change updates
        MAX_UPDATES = 10
        existing_updates = group.get("updates", [])
        new_updates = updates + existing_updates
        if len(new_updates) > MAX_UPDATES:
            new_updates = new_updates[:MAX_UPDATES]
        
        group.update({
            "members": members,
            "summary": f"Current members: {', '.join(p['name'] for p in nearby_players)}",
            "updates": new_updates,
            "last_updated": datetime.now().isoformat()
        })
        
        # Save updates (not async)
        update_memory_block(client, agent_id, "status", status)
        update_memory_block(client, agent_id, "group_members", group)
        
        logger.debug(f"Updated blocks for agent {agent_id}:")
        logger.debug(f"Status: {json.dumps(status, indent=2)}")
        logger.debug(f"Group: {json.dumps(group, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to update group status for {agent_id}: {str(e)}")
        raise

def verify_group_state(client, agent_ids: List[str], snapshot_data: Dict):
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

