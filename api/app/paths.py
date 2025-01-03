from pathlib import Path
from typing import Dict
from .config import get_game_paths

def get_database_paths(game_slug: str = "sandbox-v1"):
    """Get paths for game databases"""
    game_paths = get_game_paths(game_slug)  # Now game_slug is defined
    
    # Get paths for the specific game
    if game_slug in game_paths:
        data_dir = game_paths[game_slug]['data']
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
    return None 