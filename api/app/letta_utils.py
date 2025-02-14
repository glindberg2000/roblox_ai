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
    """This function is no longer used - all action processing happens in process_tool_results"""
    pass