"""In-memory cache for static game data"""
import logging
from typing import Dict, Optional, List
from .database import (
    get_db, 
    get_all_locations, 
    get_player_info as db_get_player_info,
    get_player_description as db_get_player_description
)

logger = logging.getLogger("roblox_app")

# Standardized cache structures
PLAYER_CACHE: Dict[str, dict] = {
    # player_id: {
    #     'id': str,
    #     'display_name': str,
    #     'description': str
    # }
}

NPC_CACHE: Dict[str, dict] = {
    # display_name: {
    #     'id': str,
    #     'system_prompt': str,
    #     'description': str
    # }
}

AGENT_ID_CACHE: Dict[str, str] = {
    # npc_id: agent_id
}

LOCATION_CACHE: Dict[str, dict] = {
    # slug: {
    #     'name': str,
    #     'coordinates': List[float]
    # }
}

def init_static_cache():
    """Initialize static data caches on server boot"""
    logger.info("Initializing static data caches...")
    refresh_npc_cache()
    refresh_location_cache()

def refresh_npc_cache():
    """Refresh NPC and agent caches"""
    GAME_ID = 74  # Hardcode for now
    try:
        with get_db() as db:
            # Get agent mappings directly first
            cursor = db.execute("""
                SELECT npc_id, letta_agent_id 
                FROM npc_agents 
                WHERE participant_id = 'letta_v3'
            """)
            agent_mappings = {row['npc_id']: row['letta_agent_id'] for row in cursor.fetchall()}
            logger.info("=== Agent Mappings from DB ===")
            for npc_id, agent_id in agent_mappings.items():
                logger.info(f"{npc_id} -> {agent_id}")

            # Then get NPC data
            cursor = db.execute("""
                SELECT 
                    n.npc_id,
                    n.display_name,
                    n.system_prompt,
                    a.description as asset_description
                FROM npcs n
                LEFT JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.game_id = ?
            """, (GAME_ID,))
            
            npcs = cursor.fetchall()
            
            # Clear existing caches
            NPC_CACHE.clear()
            AGENT_ID_CACHE.clear()
            
            # Update both NPC and agent ID caches
            logger.info("=== Caching NPCs and Agents ===")
            for npc in npcs:
                logger.info(f"Processing {npc['display_name']}")
                logger.info(f"  NPC ID: {npc['npc_id']}")
                logger.info(f"  Has agent: {npc['npc_id'] in agent_mappings}")
                
                NPC_CACHE[npc['display_name']] = {
                    'id': npc['npc_id'],
                    'system_prompt': npc['system_prompt'],
                    'description': npc['asset_description']
                }
                if npc['npc_id'] in agent_mappings:
                    AGENT_ID_CACHE[npc['npc_id']] = agent_mappings[npc['npc_id']]
                    logger.info(f"  Cached agent: {agent_mappings[npc['npc_id']]}")
            
            logger.info(f"Loaded {len(NPC_CACHE)} NPCs into cache")
            logger.info(f"Loaded {len(AGENT_ID_CACHE)} agent IDs into cache")
    except Exception as e:
        logger.error(f"Error refreshing NPC cache: {str(e)}")
        raise

def refresh_location_cache():
    """Refresh location cache from database"""
    global LOCATION_CACHE
    
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT name, slug, position_x, position_y, position_z 
                FROM assets 
                WHERE is_location = 1
            """)
            locations = cursor.fetchall()
            
            LOCATION_CACHE.clear()
            for loc in locations:
                LOCATION_CACHE[loc['slug']] = {
                    'name': loc['name'],
                    'coordinates': [loc['position_x'], loc['position_y'], loc['position_z']]
                }
                
            logger.debug("=== Location Cache ===")
            logger.debug(f"Cached {len(LOCATION_CACHE)} locations:")
            for slug, data in LOCATION_CACHE.items():
                logger.debug(f"  {slug}: {data}")
                
    except Exception as e:
        logger.error(f"Error refreshing location cache: {e}")

def get_npc_id_from_name(display_name: str) -> str:
    """Get NPC ID from display name using cache"""
    npc_data = NPC_CACHE.get(display_name)
    return npc_data['id'] if npc_data else None

def get_npc_description(display_name: str) -> str:
    """Get NPC description from cache"""
    npc_data = NPC_CACHE.get(display_name)
    return npc_data['description'] if npc_data else None 

def get_agent_id(npc_id: str) -> str:
    """Get agent ID from NPC ID using cache"""
    agent_id = AGENT_ID_CACHE.get(npc_id)
    logger.info(f"Looking up agent for NPC {npc_id}")
    logger.info(f"  Found in cache: {agent_id}")
    return agent_id

def get_player_info(player_id: str) -> Optional[Dict]:
    """Get player info from cache or database"""
    if player_id in PLAYER_CACHE:
        logger.debug(f"Cache hit for player {player_id}")
        return PLAYER_CACHE[player_id]
        
    # Cache miss - get from DB and cache it
    logger.debug(f"Cache miss for player {player_id}, fetching from DB")
    player_info = db_get_player_info(player_id)
    if player_info:
        PLAYER_CACHE[player_id] = player_info
        
    return player_info

def invalidate_player_cache(player_id: str) -> None:
    """Remove player from cache (e.g., when description updates)"""
    if player_id in PLAYER_CACHE:
        del PLAYER_CACHE[player_id]
        logger.info(f"Invalidated cache for player {player_id}") 

def get_player_description(player_id: str) -> str:
    """Get player description from cache, falling back to DB"""
    # Try cache first
    player_info = PLAYER_CACHE.get(player_id)
    if player_info and 'description' in player_info:
        logger.debug(f"Cache hit for player description {player_id}")
        return player_info['description']
        
    # Cache miss - get from DB
    logger.debug(f"Cache miss for description {player_id}, fetching from DB")
    description = db_get_player_description(player_id)
    
    # Cache the result if we got one
    if description:
        if player_id not in PLAYER_CACHE:
            PLAYER_CACHE[player_id] = {}
        PLAYER_CACHE[player_id]['description'] = description
        
    return description or "Unknown"

def update_player_cache_with_description(player_id: str, description: str):
    """Update player cache when a new description is stored"""
    if player_id not in PLAYER_CACHE:
        PLAYER_CACHE[player_id] = {}
    PLAYER_CACHE[player_id]['description'] = description
    logger.info(f"Updated PLAYER_CACHE for {player_id} with description")

# Current format needed:
LOCATION_CACHE = {
    'petes_stand': {  # Slug as key
        'name': "Pete's Merch Stand",
        'coordinates': [-6.8, 3.0, -115.0]
    },
    'chipotle': {
        'name': 'Chipotle',
        'coordinates': [8.0, 3.0, -12.0]
    }
} 

# Keep existing functions as wrappers for backward compatibility
def get_player_description(player_id: str) -> str:
    """Legacy wrapper - prefer direct PLAYER_CACHE access"""
    player_info = PLAYER_CACHE.get(player_id, {})
    return player_info.get('description', 'Unknown')

def get_npc_description(display_name: str) -> str:
    """Legacy wrapper - prefer direct NPC_CACHE access"""
    npc_info = NPC_CACHE.get(display_name, {})
    return npc_info.get('description', '')

def get_agent_id(npc_id: str) -> str:
    """Legacy wrapper - prefer direct AGENT_ID_CACHE access"""
    return AGENT_ID_CACHE.get(npc_id) 