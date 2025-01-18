"""In-memory cache for static game data"""
import logging
from typing import Dict
from .database import get_db, get_all_locations

logger = logging.getLogger("roblox_app")

# Global caches
NPC_CACHE: Dict[str, dict] = {}
LOCATION_CACHE: Dict[str, dict] = {}
AGENT_ID_CACHE: Dict[str, str] = {}

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
            # Load NPCs with asset data and agent IDs for current game
            cursor = db.execute("""
                SELECT 
                    n.id as npc_id,
                    n.display_name,
                    n.system_prompt,
                    a.description as asset_description,
                    na.letta_agent_id
                FROM npcs n
                LEFT JOIN assets a ON n.asset_id = a.id
                LEFT JOIN npc_agents na ON n.npc_id = na.npc_id 
                WHERE n.game_id = ? 
                    AND (na.participant_id = 'letta_v3' OR na.participant_id IS NULL)
            """, (GAME_ID,))
            
            npcs = cursor.fetchall()
            
            # Clear existing caches
            NPC_CACHE.clear()
            AGENT_ID_CACHE.clear()
            
            # Update both NPC and agent ID caches
            for npc in npcs:
                NPC_CACHE[npc['display_name']] = {
                    'id': npc['npc_id'],
                    'system_prompt': npc['system_prompt'],
                    'description': npc['asset_description']
                }
                if npc['letta_agent_id']:  # Only cache if agent exists
                    AGENT_ID_CACHE[npc['npc_id']] = npc['letta_agent_id']
            
            logger.info(f"Loaded {len(NPC_CACHE)} NPCs into cache")
            logger.info(f"Loaded {len(AGENT_ID_CACHE)} agent IDs into cache")
    except Exception as e:
        logger.error(f"Error refreshing NPC cache: {str(e)}")
        raise

def refresh_location_cache():
    """Refresh location cache"""
    try:
        # Use get_all_locations instead of direct DB query
        locations = get_all_locations()
        
        LOCATION_CACHE.clear()
        for loc in locations:
            LOCATION_CACHE[loc['slug']] = {
                'name': loc['name'],
                'description': loc['description'],
                'coordinates': loc['coordinates']
            }
        logger.info(f"Loaded {len(LOCATION_CACHE)} locations into cache")
        
    except Exception as e:
        logger.error(f"Error refreshing location cache: {str(e)}")
        raise

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
    return AGENT_ID_CACHE.get(npc_id) 