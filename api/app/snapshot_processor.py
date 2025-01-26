from typing import Dict, Optional, List
import math
import logging
from .cache import LOCATION_CACHE
from .models import GameSnapshot, PositionData, HumanContextData, GroupData
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Store previous snapshot for comparison
last_snapshot: Dict = {}

def update_previous_state(snapshot_data: GameSnapshot):
    """Update the previous state cache"""
    global last_snapshot
    last_snapshot = snapshot_data.model_dump()

def get_previous_entity_state() -> Dict:
    """Get previous snapshot state"""
    global last_snapshot
    if last_snapshot and 'humanContext' in last_snapshot:
        return last_snapshot['humanContext']
    return {}

def get_entity_previous_state(entity_id: str) -> Optional[Dict]:
    """Get specific entity's state from previous snapshot"""
    previous = get_previous_entity_state()
    return previous.get(entity_id)

def generate_health_context(old_health: Dict, new_health: Dict) -> str:
    """Generate narrative about health changes"""
    if not old_health or not new_health:
        return ""
        
    narratives = []
    
    # Check for death state
    if new_health.get('state') == 'Dead':
        if old_health.get('state') != 'Dead':
            narratives.append('Died')
            if new_health['current'] == 0:
                narratives.append('Took fatal damage')
    
    # Check for resurrection
    if old_health.get('state') == 'Dead' and new_health.get('state') != 'Dead':
        narratives.append('Resurrected')
    
    # Check for unusual health states
    if new_health['max'] == 0:
        narratives.append("In an unusual health state")
    
    # Check for health changes
    health_diff = new_health['current'] - old_health['current']
    if health_diff < -20:
        narratives.append(f"Took severe damage (-{abs(health_diff)})")
    elif health_diff < 0:
        narratives.append("Took minor damage")
    elif health_diff > 20:
        narratives.append(f"Recovered significantly (+{health_diff})")
    elif health_diff > 0:
        narratives.append("Slowly recovering")
    
    return " | ".join(narratives) if narratives else ""

def generate_activity_context(old_state: Dict, new_state: Dict) -> str:
    """Generate narrative about entity's activities and state changes"""
    if not old_state or not new_state:
        return ""
        
    narratives = []
    
    # Get health states
    old_health = old_state.get('health', {})
    new_health = new_state.get('health', {})
    
    current_state = new_health.get('state', '')
    previous_state = old_health.get('state', '')
    
    # State changes first
    if current_state != previous_state:
        if previous_state == 'Running':
            narratives.append("Stopped running")
        elif previous_state == 'Walking':
            narratives.append("Stopped walking")
        elif previous_state == 'Dancing':
            narratives.append("Stopped dancing")
    
    # Handle emotes
    if current_state == 'Emoting':
        emote_data = new_state.get('emote', {})
        if emote_data:
            if emote_data.get('name') == 'Wave' and emote_data.get('target'):
                narratives.append(f"Waving at {emote_data['target']}")
            elif emote_data.get('name') == 'Dance':
                if emote_data.get('style'):
                    narratives.append(f"Dancing {emote_data['style']} style")
                else:
                    narratives.append("Dancing")
            else:
                narratives.append("Performing emote")
        else:
            narratives.append("Performing emote")  # Default if no emote data
    
    # Handle movement states
    elif current_state == 'Running':
        is_moving = new_health.get('isMoving', False)
        if is_moving:
            narratives.append("Running")
        else:
            narratives.append("Standing")
    elif current_state == 'Jumping':
        narratives.append("Just jumped")
    elif current_state == 'Walking':
        narratives.append("Walking")
    elif current_state == 'Idle':
        narratives.append("Standing still")
    
    return " | ".join(narratives) if narratives else ""

def _generate_group_updates(old_members: List[str], new_members: List[str]) -> List[str]:
    """Generate narrative updates for group membership changes"""
    old_set = set(old_members)
    new_set = set(new_members)
    
    updates = []
    
    # Check for joins
    joined = new_set - old_set
    if joined:
        # Sort alphabetically for consistent order
        sorted_joined = sorted(joined)
        updates.append(f"{', '.join(sorted_joined)} joined the group")
    
    # Check for leaves
    left = old_set - new_set
    if left:
        sorted_left = sorted(left)
        updates.append(f"{', '.join(sorted_left)} left the group")
    
    return updates

def enrich_snapshot_with_context(snapshot: GameSnapshot) -> GameSnapshot:
    """Add rich context to snapshot data"""
    logger.debug(f"=== Starting snapshot enrichment ===")
    
    # Get previous state for comparison
    previous_state = get_previous_entity_state()
    
    for entity_id, context_dict in snapshot.humanContext.items():
        logger.debug(f"\nProcessing entity: {entity_id}")
        
        # Convert raw dict to HumanContextData model
        context = HumanContextData(**context_dict)
        logger.debug(f"Raw context data: {context.model_dump()}")
        
        # Process position if available
        if context.position:
            nearest_location = context.position.get_nearest_location()
            location_narrative = context.position.get_location_narrative()
            logger.debug(f"Location narrative: {location_narrative}")
            
            # Update context with enriched location data
            context.location = nearest_location
            
            # Add narrative to recent interactions
            if context.recentInteractions:
                context.recentInteractions[-1]["narrative"] = location_narrative
        
        # Process group changes if we have previous state
        if previous_state and entity_id in previous_state:
            prev_context = previous_state[entity_id]
            if 'currentGroups' in prev_context:
                old_members = prev_context['currentGroups']['members']
                new_members = context.currentGroups.members
                
                updates = _generate_group_updates(old_members, new_members)
                if updates:
                    # Create new group data with updates
                    context.currentGroups = GroupData(
                        members=new_members,
                        npcs=context.currentGroups.npcs,
                        players=context.currentGroups.players,
                        formed=context.currentGroups.formed,
                        updates=updates
                    )
        
        # Update the snapshot with enriched context
        snapshot.humanContext[entity_id] = context.model_dump()
    
    # Store current state for next comparison
    update_previous_state(snapshot)
    
    return snapshot 