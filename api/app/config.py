# api/app/config.py

import os
from pathlib import Path

# Base directory is the api folder
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database paths
DB_DIR = BASE_DIR / "db"
SQLITE_DB_PATH = DB_DIR / "game_data.db"

# Add missing game paths function and directory
GAMES_DIR = Path(os.path.dirname(BASE_DIR)) / "games"

def get_game_paths(game_slug=None):
    """Get paths for all game directories"""
    if not GAMES_DIR.exists():
        return {}
    
    if game_slug:
        game_dir = GAMES_DIR / game_slug
        if game_dir.is_dir():
            return {
                game_slug: {
                    'root': game_dir,
                    'data': game_dir / 'src' / 'data',
                    'assets': game_dir / 'src' / 'assets'
                }
            }
        return {}
    
    # Return all game directories
    return {
        d.name: {
            'root': d,
            'data': d / 'src' / 'data',
            'assets': d / 'src' / 'assets'
        }
        for d in GAMES_DIR.iterdir() 
        if d.is_dir()
    }

# Storage structure
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = STORAGE_DIR / "assets"  # For RBXMX files
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"  # For asset thumbnails from Roblox CDN
AVATARS_DIR = STORAGE_DIR / "avatars"  # For player avatar images

# Ensure all directories exist
for directory in [STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Roblox project paths (new additions)
ROBLOX_DIR = Path(os.path.dirname(BASE_DIR)) / "src"
ROBLOX_ASSETS_DIR = ROBLOX_DIR / "assets"
ROBLOX_DATA_DIR = ROBLOX_DIR / "data"

# Ensure Roblox directories exist
for directory in [ROBLOX_ASSETS_DIR, ROBLOX_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API URLs
ROBLOX_API_BASE = "https://thumbnails.roblox.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Security settings
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "your-secure-admin-key")
GAME_API_KEY = os.getenv("GAME_API_KEY", "your-game-integration-key")

# LLM settings
DEFAULT_LLM = os.getenv("DEFAULT_LLM", "gpt-4o-mini")

# LLM configuration
LLM_CONFIGS = {
    "gpt-4o-mini": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "model_endpoint_type": "openai",
        "model_endpoint": "https://api.openai.com/v1",
        "context_window": 128000
    }
}

# Embedding configuration
DEFAULT_EMBEDDING = os.getenv("DEFAULT_EMBEDDING", "text-embedding-ada-002")
EMBEDDING_CONFIGS = {
    "text-embedding-ada-002": {
        "embedding_model": "text-embedding-ada-002",
        "embedding_dim": 1536,
        "embedding_endpoint_type": "openai",
        "context_window": 128000,
        "normalize": True
    }
}

NPC_SYSTEM_PROMPT_ADDITION = """
When responding, always use the appropriate action type:
- Use "follow" when you intend to start following the player.
- Use "unfollow" when you intend to stop following the player.
- Use "stop_talking" when you want to end the conversation.
- Use "none" for any other response that doesn't require a specific action.

Your response must always include an action, even if it's "none".
"""