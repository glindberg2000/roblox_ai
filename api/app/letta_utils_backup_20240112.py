"""Utilities for handling Letta responses"""
import json
from typing import Dict, Any
import logging

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
    logger.info("Starting tool result extraction")
    result = {
        'tool_calls': [],      # Store all tool interactions
        'llm_response': None,  # Final text response
        'internal_thoughts': []  # Internal monologue entries
    }
    
    if not hasattr(response, 'messages'):
        logger.warning("Response has no messages attribute")
        return result
        
    logger.info(f"Processing {len(response.messages)} messages")
    for msg in response.messages:
        logger.info(f"Processing message type: {type(msg)}")
        
        # Capture tool calls and their results
        if hasattr(msg, 'function_call'):
            logger.info(f"Found function call: {msg.function_call.name}")
            tool_call = {
                'name': msg.function_call.name,
                'arguments': None,
                'result': None,
                'status': None
            }
            
            # Parse arguments if present
            try:
                tool_call['arguments'] = json.loads(msg.function_call.arguments)
                logger.info(f"Parsed arguments: {tool_call['arguments']}")
            except Exception as e:
                logger.error(f"Failed to parse arguments: {e}")
                tool_call['arguments'] = msg.function_call.arguments
                
            result['tool_calls'].append(tool_call)
            
        # Capture tool results
        elif hasattr(msg, 'function_return'):
            logger.info("Found function return")
            if result['tool_calls']:
                try:
                    return_data = json.loads(msg.function_return)
                    logger.info(f"Parsed return data: {return_data}")
                    result['tool_calls'][-1].update({
                        'result': return_data,
                        'status': msg.status
                    })
                except Exception as e:
                    logger.error(f"Failed to parse return data: {e}")
                    result['tool_calls'][-1].update({
                        'result': msg.function_return,
                        'status': msg.status
                    })
                    
        # Capture LLM's text response
        elif hasattr(msg, 'text') and msg.text:
            logger.info(f"Found text response: {msg.text[:100]}...")
            result['llm_response'] = msg.text
            
        # Capture internal thoughts
        elif hasattr(msg, 'internal_monologue'):
            logger.info("Found internal monologue")
            result['internal_thoughts'].append(msg.internal_monologue)
    
    logger.info(f"Extraction complete. Found {len(result['tool_calls'])} tool calls")
    return result