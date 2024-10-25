# api/app/config.py

import os
from pathlib import Path

# Base directory is the api folder
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Storage structure
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = STORAGE_DIR / "assets"  # For RBXMX files
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"  # For asset thumbnails from Roblox CDN
AVATARS_DIR = STORAGE_DIR / "avatars"  # For player avatar images

# Ensure all directories exist
for directory in [STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API URLs
ROBLOX_API_BASE = "https://thumbnails.roblox.com/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


NPC_SYSTEM_PROMPT_ADDITION = """
When responding, always use the appropriate action type:
- Use "follow" when you intend to start following the player.
- Use "unfollow" when you intend to stop following the player.
- Use "stop_talking" when you want to end the conversation.
- Use "none" for any other response that doesn't require a specific action.

Your response must always include an action, even if it's "none".
"""

