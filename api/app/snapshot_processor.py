from typing import Dict, Optional
import math
import logging
from .cache import LOCATION_CACHE
from .models import GameSnapshot, PositionData
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Store previous snapshot for comparison
last_snapshot: Dict = {}

def update_previous_state(snapshot_data: GameSnapshot):
    """Update the previous state cache"""
    global last_snapshot
    last_snapshot = snapshot_data.dict()

def get_previous_entity_state(entity_id: str) -> Optional[Dict]:
    """Get entity's state from previous snapshot"""
    if last_snapshot and 'humanContext' in last_snapshot:
        return last_snapshot['humanContext'].get(entity_id)
    return None

def generate_health_context(old_health: Dict, new_health: Dict) -> str:
    """Generate narrative about health changes"""
    if not old_health or not new_health:
        return ""
        
    narratives = []
    
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
    
    # Check state changes
    if old_health['state'] != new_health['state']:
        narratives.append(f"State changed to {new_health['state']}")
    
    return " | ".join(narratives) if narratives else "" 

def generate_activity_context(old_state: Dict, new_state: Dict) -> str:
    """Generate narrative about entity's activities and state changes"""
    if not old_state or not new_state:
        return ""
        
    logger.debug(f"Generating activity context:")
    logger.debug(f"Full old state: {json.dumps(old_state, indent=2)}")
    logger.debug(f"Full new state: {json.dumps(new_state, indent=2)}")
    
    narratives = []
    
    # Movement state from health
    if 'health' in new_state and 'health' in old_state:
        current_state = new_state['health'].get('state', '')
        previous_state = old_state['health'].get('state', '')
        
        # Safely handle velocity
        current_velocity = new_state.get('velocity', None)
        is_moving = False
        if current_velocity:
            try:
                if len(current_velocity) >= 3:
                    # Increase threshold slightly and check horizontal movement only
                    horizontal_movement = abs(current_velocity[0]) + abs(current_velocity[2])  # x + z
                    is_moving = horizontal_movement > 0.2  # Slightly higher threshold
            except Exception as e:
                logger.error(f"Error processing velocity: {e}")
                is_moving = False
        
        logger.info(f"Health states: {previous_state} -> {current_state} (Moving: {is_moving})")
        
        # Only show running if actually moving
        if current_state == "Running":
            if is_moving:  # Must be actually moving
                narratives.append("Running")
            else:
                narratives.append("Standing")  # They're in run animation but not moving
        elif current_state == "Walking":
            narratives.append("Walking")
        elif current_state == "Idle":
            narratives.append("Standing still")
            
        # Only mention changes
        if current_state != previous_state:
            if current_state == "Jumping":
                narratives.append("Just jumped")
            elif current_state == "Emoting":
                narratives.append("Performing emote")
            elif previous_state == "Running" and current_state != "Running":
                narratives.append("Stopped running")
    
    narrative = " | ".join(narratives) if narratives else ""
    logger.debug(f"Generated activity narrative: {narrative}")
    return narrative

def enrich_snapshot_with_context(snapshot: GameSnapshot) -> GameSnapshot:
    """Add rich context to snapshot data"""
    logger.debug(f"=== Starting snapshot enrichment ===")
    
    for entity_id, context in snapshot.humanContext.items():
        logger.debug(f"\nProcessing entity: {entity_id}")
        logger.debug(f"Raw context data: {context.dict()}")
        
        narratives = []
        previous_state = get_previous_entity_state(entity_id)
        
        if previous_state:
            logger.debug(f"Previous state: {previous_state}")
        
        # Debug health data specifically
        if hasattr(context, 'health'):
            logger.debug(f"Health data: {context.health}")
            
            # Activity context first
            activity_narrative = generate_activity_context(
                previous_state,
                context.dict()
            )
            if activity_narrative:
                narratives.append(activity_narrative)
                logger.debug(f"Added activity narrative: {activity_narrative}")
        else:
            logger.debug(f"No health data found for {entity_id}")
        
        # Location context
        if context.position:
            context.location = context.position.get_nearest_location()
            if previous_state and previous_state.get('position'):
                narratives.append(context.position.get_location_narrative())
        
        # Group context
        if context.currentGroups and context.currentGroups.members:
            others = [m for m in context.currentGroups.members if m != entity_id]
            if others:
                narratives.append(f"With {', '.join(others)}")
        
        # Store narrative
        if narratives:
            context.recentInteractions.append({
                'timestamp': snapshot.timestamp,
                'narrative': ' | '.join(narratives)
            })
    
    update_previous_state(snapshot)
    return snapshot 