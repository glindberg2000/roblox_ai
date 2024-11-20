"""Test script for Lua generation utilities"""
import sys
from pathlib import Path
import json
import logging
import argparse

# Add api directory to path so we can import utils
api_path = Path(__file__).parent.parent / "api"
sys.path.append(str(api_path))

from app.utils import generate_lua_from_db
from app.config import SQLITE_DB_PATH

def test_npc_lua_generation(game_slug: str):
    """Test NPC data export using actual utils function"""
    # Configure test logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_lua")
    
    try:
        # Generate Lua using actual utility with specified game
        logger.info(f"\nGenerating Lua for game: {game_slug}")
        generate_lua_from_db(game_slug, 'npc')
        
        # Verify the file was created
        game_lua_path = Path("games") / game_slug / "src" / "data" / "NPCDatabase.lua"
        if game_lua_path.exists():
            logger.info(f"\nSuccessfully generated Lua file at: {game_lua_path}")
            logger.info("\nFile contents:")
            logger.info(game_lua_path.read_text())
            return True
        else:
            logger.error(f"Lua file not found at: {game_lua_path}")
            return False
            
    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Lua file generation for a game')
    parser.add_argument('game_slug', help='The game slug to generate Lua for (e.g., sandbox-v1)')
    
    args = parser.parse_args()
    success = test_npc_lua_generation(args.game_slug)
    sys.exit(0 if success else 1) 