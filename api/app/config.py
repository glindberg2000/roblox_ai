# api/app/config.py

import os
from pathlib import Path

# Base directory is the api folder
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database paths
DB_DIR = BASE_DIR / "db"
SQLITE_DB_PATH = DB_DIR / "game_data.db"

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)

# Storage structure
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = STORAGE_DIR / "assets"  # For RBXMX files
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"  # For asset thumbnails from Roblox CDN
AVATARS_DIR = STORAGE_DIR / "avatars"  # For player avatar images

# Ensure all directories exist
for directory in [STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Replace hard-coded ROBLOX_DIR with dynamic game-specific paths
def get_game_paths(game_slug: str) -> dict:
    """Get game-specific paths"""
    game_dir = Path(os.path.dirname(BASE_DIR)) / "games" / game_slug
    return {
        'root': game_dir,
        'src': game_dir / "src",
        'assets': game_dir / "src" / "assets",
        'data': game_dir / "src" / "data"
    }

def ensure_game_directories(game_slug: str) -> None:
    """Ensure all required directories exist for a specific game"""
    paths = get_game_paths(game_slug)
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

# API URLs
ROBLOX_API_BASE = "https://thumbnails.roblox.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# NPC Configuration
NPC_SYSTEM_PROMPT_ADDITION = """
When responding, always use the appropriate action type:
- Use "follow" when you intend to start following the player.
- Use "unfollow" when you intend to stop following the player.
- Use "stop_talking" when you want to end the conversation.
- Use "none" for any other response that doesn't require a specific action.

Your response must always include an action, even if it's "none".
"""
