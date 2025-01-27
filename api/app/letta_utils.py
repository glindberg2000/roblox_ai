"""Utilities for handling Letta responses"""
import json
import logging
from typing import Dict, Any, List
from .cache import LOCATION_CACHE  # Import the cache

logger = logging.getLogger(__name__)

def extract_action_result(response) -> Dict[str, Any]:
    """
    Extract action results and messages from Letta response
    Based on letta_quickstart.extract_action_result
    """
    result = {
        'action_status': "none",
        'action_message': "No action message",
        'llm_response': "I'm having trouble responding right now."
    }
    
    if hasattr(response, 'messages'):
        for msg in response.messages:
            # Get function return (action result)
            if hasattr(msg, 'function_return'):
                try:
                    action_result = json.loads(msg.function_return)
                    if action_result.get('status'):
                        result['action_status'] = action_result['status']
                    if action_result.get('message'):
                        result['action_message'] = action_result['message']
                except:
                    pass
                    
            # Get final LLM response
            elif hasattr(msg, 'text') and msg.text:
                result['llm_response'] = msg.text
                
    return result

def create_tool_enabled_agent(client, name: str, **kwargs):
    """
    Create a Letta agent with NPC tools enabled
    Based on letta_quickstart.create_personalized_agent
    """
    return client.create_agent(
        name=name,
        include_base_tools=True,
        description="A Roblox NPC with action capabilities",
        **kwargs
    ) 

def extract_tool_results(response):
    """
    Extract all tool calls, results, and messages from a response.
    """
    result = {
        'tool_calls': [],      # Store all tool interactions
        'llm_response': None,  # Final text response
        'internal_thoughts': []  # Internal monologue entries
    }
    
    if not hasattr(response, 'messages'):
        return result
        
    for msg in response.messages:
        # Capture tool calls and their results
        if hasattr(msg, 'function_call'):
            tool_call = {
                'name': msg.function_call.name,
                'arguments': None,
                'result': None,
                'status': None
            }
            
            # Parse arguments if present
            try:
                tool_call['arguments'] = json.loads(msg.function_call.arguments)
            except:
                tool_call['arguments'] = msg.function_call.arguments
                
            # Find corresponding result for this tool call
            result['tool_calls'].append(tool_call)
            
        # Capture tool results
        elif hasattr(msg, 'function_return'):
            # Only process if we have tool calls
            if result['tool_calls']:
                try:
                    return_data = json.loads(msg.function_return)
                    result['tool_calls'][-1].update({
                        'result': return_data,
                        'status': msg.status
                    })
                except:
                    result['tool_calls'][-1].update({
                        'result': msg.function_return,
                        'status': msg.status
                    })
                    
        # Capture LLM's text response
        elif hasattr(msg, 'text') and msg.text:
            result['llm_response'] = msg.text
            
        # Capture internal thoughts
        elif hasattr(msg, 'internal_monologue'):
            result['internal_thoughts'].append(msg.internal_monologue)
    
    return result

def convert_tool_calls_to_action(tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert Letta tool calls to Roblox action format
    
    Expected Roblox format:
    {
        type = "navigate"|"follow"|"unfollow"|"emote"|"end_conversation",
        data = {
            # For navigate:
            coordinates = {x: float, y: float, z: float}
            
            # For follow:
            target = str  # player name
            
            # For emote:
            emote_type = str  # wave|laugh|dance|cheer|point|sit
            target = str  # Optional target name
        }
    }
    """
    if not tool_calls:
        return {"type": "none"}
        
    # Get first tool call
    tool = tool_calls[0]
    logger.debug(f"Converting tool to action: {tool}")
    
    if tool["tool"] == "perform_action":
        args = tool["args"]
        action_type = args.get("action")
        
        if action_type == "follow":
            return {
                "type": "follow",
                "data": {
                    "target": args.get("target")
                }
            }
        elif action_type == "unfollow":
            return {
                "type": "unfollow",
                "data": {}
            }
        elif action_type == "emote":
            data = {
                "emote_type": args.get("type")
            }
            if args.get("target"):
                data["target"] = args["target"]
            return {
                "type": "emote",
                "data": data
            }
            
    elif tool["tool"] == "navigate_to":
        # Get coordinates directly from cache
        slug = tool["args"].get("destination_slug")
        if slug and slug in LOCATION_CACHE:
            location = LOCATION_CACHE[slug]
            return {
                "type": "navigate",
                "data": {
                    "coordinates": {
                        "x": location["coordinates"][0],
                        "y": location["coordinates"][1],
                        "z": location["coordinates"][2]
                    }
                }
            }
            
    elif tool["tool"] == "navigate_to_coordinates":
        # Handle direct coordinate navigation
        args = tool["args"]
        return {
            "type": "navigate",
            "data": {
                "coordinates": {
                    "x": float(args.get("x", 0)),
                    "y": float(args.get("y", 0)),
                    "z": float(args.get("z", 0))
                }
            }
        }
        
    logger.debug(f"Unknown tool type: {tool['tool']}")
    return {"type": "none"}