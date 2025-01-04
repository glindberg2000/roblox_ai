from fastapi import APIRouter, HTTPException, Depends, Request
from letta import (
    ChatMemory, 
    LLMConfig, 
    EmbeddingConfig, 
    create_client,
    BasicBlockMemory
)
from letta.prompts import gpt_system
from letta_roblox.client import LettaRobloxClient
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel
from .database import (
    get_npc_context, 
    create_agent_mapping, 
    get_agent_mapping, 
    get_db, 
    get_player_info,
    get_location_coordinates,
    get_all_locations
)
from .mock_player import MockPlayer
from .config import (
    DEFAULT_LLM, 
    LLM_CONFIGS, 
    EMBEDDING_CONFIGS, 
    DEFAULT_EMBEDDING
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
            logger.info(f"Message details:")
            logger.info(f"  agent_id: {agent_mapping.letta_agent_id}")
            logger.info(f"  role: {message_role}")
            logger.info(f"  message: {request.message}")
            logger.info(f"  direct_client: {direct_client}")
            
            response = direct_client.send_message(
                agent_id=agent_mapping.letta_agent_id,
                role=message_role,
                message=request.message
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
    """New endpoint using direct Letta SDK"""
    try:
        # Basic request logging
        logger.info(f"Received request from game: {request.model_dump_json()}")

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
            logger.info(f"Message details:")
            logger.info(f"  agent_id: {agent_mapping.letta_agent_id}")
            logger.info(f"  role: {message_role}")
            logger.info(f"  message: {request.message}")
            logger.info(f"  direct_client: {direct_client}")
            
            response = direct_client.send_message(
                agent_id=agent_mapping.letta_agent_id,
                role=message_role,
                message=request.message
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

