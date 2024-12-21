"""NPC Tool Definitions for Letta Integration"""
from typing import Dict, Callable, Optional
import datetime
from dataclasses import dataclass
from enum import Enum

# State enums for consistency
class ActionProgress(Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ActionState:
    """Base state information for actions"""
    current_action: str
    progress: str
    position: str
    can_interact: bool = True
    interruption_allowed: bool = True

def _format_action_message(action: str, target: Optional[str], state: ActionState) -> str:
    """Format natural language message for actions"""
    messages = {
        "follow": f"I am now following {target}. I'll maintain a respectful distance.",
        "wave": f"I'm waving{' at ' + target if target else ''}!",
        "sit": "I've taken a seat. Feel free to continue our conversation."
    }
    
    return messages.get(action, f"Performing action: {action}{' targeting ' + target if target else ''}")

def perform_action(action: str, target: Optional[str] = None, request_heartbeat: bool = True) -> dict:
    """Perform a basic NPC action like following or emoting."""
    states = {
        "follow": ActionState(
            current_action="following",
            progress=ActionProgress.IN_PROGRESS.value,
            position="maintaining follow distance",
            can_interact=True,
            interruption_allowed=True
        ),
        "wave": ActionState(
            current_action="waving",
            progress=ActionProgress.IN_PROGRESS.value,
            position="in place",
            can_interact=False,
            interruption_allowed=True
        ),
        "sit": ActionState(
            current_action="sitting",
            progress=ActionProgress.COMPLETED.value,
            position="stationary",
            can_interact=True,
            interruption_allowed=True
        )
    }
    
    state = states.get(action, ActionState(
        current_action=action,
        progress=ActionProgress.IN_PROGRESS.value,
        position="unknown",
    ))
    
    return {
        "status": "success",
        "action_called": action,
        "state": {
            "current_action": state.current_action,
            "target": target,
            "progress": state.progress,
            "position": state.position
        },
        "context": {
            "can_interact": state.can_interact,
            "interruption_allowed": state.interruption_allowed,
            "target_type": "player" if target else None
        },
        "message": _format_action_message(action, target, state),
        "timestamp": datetime.datetime.now().isoformat()
    }

def navigate_to(destination: str, request_heartbeat: bool = True) -> dict:
    """
    Navigate to a specified location in the game world.
    
    Args:
        destination (str): The destination name or coordinate string
        request_heartbeat (bool): Request heartbeat after execution
        
    Returns:
        dict: Rich navigation result with state information
    """
    state = ActionState(
        current_action="moving",
        progress=ActionProgress.INITIATED.value,
        position="moving towards destination"
    )
    
    return {
        "status": "success",
        "action_called": "navigate",
        "state": {
            "current_action": state.current_action,
            "destination": destination,
            "progress": state.progress,
            "position": state.position
        },
        "context": {
            "can_interact": state.can_interact,
            "interruption_allowed": state.interruption_allowed,
            "estimated_time": "in progress"
        },
        "message": (
            f"I am now moving towards {destination}. "
            "I'll let you know when I arrive. "
            "Feel free to give me other instructions while I'm on my way."
        ),
        "timestamp": datetime.datetime.now().isoformat()
    }

def examine_object(object_name: str, request_heartbeat: bool = True) -> dict:
    """
    Examine an object in the game world.
    
    Args:
        object_name (str): Name of the object to examine
        request_heartbeat (bool): Request heartbeat after execution
        
    Returns:
        dict: Rich examination result with state information
    """
    state = ActionState(
        current_action="examining",
        progress=ActionProgress.IN_PROGRESS.value,
        position="at examination distance"
    )
    
    return {
        "status": "success",
        "action_called": "examine",
        "state": {
            "current_action": state.current_action,
            "target": object_name,
            "progress": state.progress,
            "position": state.position
        },
        "context": {
            "can_interact": state.can_interact,
            "focus": object_name,
            "observation_complete": False,
            "interruption_allowed": state.interruption_allowed
        },
        "message": (
            f"I am examining the {object_name} carefully. "
            "I can describe what I observe or interact with it further."
        ),
        "timestamp": datetime.datetime.now().isoformat()
    }

# Tool registry with metadata
TOOL_REGISTRY: Dict[str, Dict] = {
    "perform_action": {
        "function": perform_action,
        "version": "2.0.0",
        "supports_state": True,
        "allowed_actions": ["follow", "wave", "sit"]
    },
    "navigate_to": {
        "function": navigate_to,
        "version": "2.0.0",
        "supports_state": True
    },
    "examine_object": {
        "function": examine_object,
        "version": "2.0.0",
        "supports_state": True
    }
}

def get_tool(name: str) -> Callable:
    """Get tool function from registry"""
    return TOOL_REGISTRY[name]["function"] 