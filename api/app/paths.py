from pathlib import Path
from typing import Dict
from .config import get_game_paths

def get_database_paths(game_slug: str = "game1") -> Dict[str, Dict[str, Path]]:
    """
    Get paths to database files for a specific game
    
    Args:
        game_slug (str): The game identifier (e.g., "game1", "game2")
        
    Returns:
        Dict containing paths to JSON and Lua database files
    """
    game_paths = get_game_paths(game_slug)
    data_dir = game_paths['data']
    
    # Ensure the data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        'asset': {
            'json': data_dir / 'AssetDatabase.json',
            'lua': data_dir / 'AssetDatabase.lua'
        },
        'npc': {
            'json': data_dir / 'NPCDatabase.json',
            'lua': data_dir / 'NPCDatabase.lua'
        }
    } 