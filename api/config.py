from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "db"
SQLITE_DB_PATH = DB_DIR / "roblox.db"

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_DEBUG = True

# Game settings
DEFAULT_GAME = {
    "name": "Default Game",
    "slug": "default-game",
    "description": "Default game configuration"
} 