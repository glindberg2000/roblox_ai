import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional
from .config import get_game_paths, BASE_DIR, GAMES_DIR
from .db import get_db
import os
import shutil
import logging

# Set up logger
logger = logging.getLogger("roblox_app")

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

def load_json_database(path: Path) -> dict:
    """Load a JSON database file"""
    try:
        if not path.exists():
            return {"assets": [], "npcs": []}
            
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON database from {path}: {e}")
        return {"assets": [], "npcs": []}

def save_json_database(path: Path, data: dict) -> None:
    """Save data to a JSON database file"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON database to {path}: {e}")
        raise

def format_npc_as_lua(npc: dict, db: sqlite3.Connection) -> str:
    """Format a single NPC as Lua code"""
    try:
        # Handle abilities - could be string or list
        abilities_raw = npc.get('abilities', '[]')
        if isinstance(abilities_raw, list):
            abilities = abilities_raw  # Already a list
        else:
            abilities = json.loads(abilities_raw)  # Parse JSON string
            
        # Format abilities as Lua table
        abilities_lua = "{\n" + "".join(f'                "{ability}",\n' for ability in abilities) + "            }"
            
        # Handle spawn position - could be string or dict
        spawn_pos_raw = npc.get('spawnPosition', '{"x": 0, "y": 5, "z": 0}')
        if isinstance(spawn_pos_raw, dict):
            spawn_pos = spawn_pos_raw  # Already a dict
        else:
            spawn_pos = json.loads(spawn_pos_raw)  # Parse JSON string
            
        # Format spawn position as Vector3
        vector3 = f"Vector3.new({spawn_pos['x']}, {spawn_pos['y']}, {spawn_pos['z']})"

        # Use the assetId as the model name
        model = npc['assetId']
            
        return f"""        {{
            id = "{npc['id']}",
            displayName = "{npc['displayName']}",
            assetId = "{npc['assetId']}",
            model = "{model}",
            systemPrompt = "{npc.get('system_prompt', '')}",
            responseRadius = {npc.get('responseRadius', 20)},
            spawnPosition = {vector3},
            abilities = {abilities_lua},
            shortTermMemory = {{}}
        }},\n"""
    except Exception as e:
        logger.error(f"Error formatting NPC as Lua: {e}")
        logger.error(f"NPC data: {npc}")
        raise

def save_lua_database(file_path, data, db=None):
    """Save data as Lua module"""
    try:
        if 'npcs' in data:
            lua_content = "return {\n    npcs = {\n"  # Start with npcs table
            for npc in data['npcs']:
                lua_content += format_npc_as_lua(npc, db)
            lua_content += "    }\n"  # Close npcs table
            lua_content += "}\n"  # Close return table
            
            logger.info(f"Generated Lua content:\n{lua_content}")
            
            with open(file_path, 'w') as f:
                f.write(lua_content)
                
            logger.info(f"Successfully wrote Lua file to: {file_path}")
            
    except Exception as e:
        logger.error(f"Error saving Lua database: {e}")
        logger.error(f"Data: {data}")
        raise

def generate_lua_from_db(game_slug: str, db_type: str) -> None:
    """Generate Lua file directly from database data"""
    with get_db() as db:
        db.row_factory = sqlite3.Row
        
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        if db_type == 'asset':
            # Get assets from database
            cursor = db.execute("""
                SELECT asset_id, name, description, type, tags, image_url
                FROM assets WHERE game_id = ?
            """, (game_id,))
            assets = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file
            save_lua_database(db_paths['asset']['lua'], {
                "assets": [{
                    "assetId": asset["asset_id"],
                    "name": asset["name"],
                    "description": asset.get("description", ""),
                    "type": asset.get("type", "unknown"),
                    "imageUrl": asset.get("image_url", ""),
                    "tags": json.loads(asset.get("tags", "[]"))
                } for asset in assets]
            })
            
        elif db_type == 'npc':
            # Get NPCs from database
            cursor = db.execute("""
                SELECT npc_id, display_name, asset_id, model, system_prompt,
                       response_radius, spawn_position, abilities
                FROM npcs WHERE game_id = ?
            """, (game_id,))
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file - pass db connection
            save_lua_database(db_paths['npc']['lua'], {
                "npcs": [{
                    "id": npc["npc_id"],
                    "displayName": npc["display_name"],
                    "assetId": npc["asset_id"],
                    "model": npc.get("model", ""),
                    "system_prompt": npc.get("system_prompt", ""),
                    "responseRadius": npc.get("response_radius", 20),
                    "spawnPosition": json.loads(npc.get("spawn_position", "{}")),
                    "abilities": json.loads(npc.get("abilities", "[]")),
                    "shortTermMemory": []
                } for npc in npcs]
            }, db)  # Pass the db connection here

def sync_game_files(game_slug: str) -> None:
    """Sync both JSON and Lua files from database"""
    generate_lua_from_db(game_slug, 'asset')
    generate_lua_from_db(game_slug, 'npc')

def ensure_game_directories(game_slug: str) -> Dict[str, Path]:
    """Create and return game directory structure"""
    print("Starting ensure_game_directories")
    try:
        logger.info(f"Games directory: {GAMES_DIR}")
        logger.info(f"Games directory exists: {GAMES_DIR.exists()}")
        
        # Create GAMES_DIR if it doesn't exist
        GAMES_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Created or verified GAMES_DIR exists")
        
        game_root = GAMES_DIR / game_slug
        logger.info(f"Game root will be: {game_root}")
        
        # Copy from template location
        template_dir = GAMES_DIR / "_template"
        logger.info(f"Looking for template at: {template_dir}")
        logger.info(f"Template directory exists: {template_dir.exists()}")
        
        if not template_dir.exists():
            logger.error(f"Template directory not found at: {template_dir}")
            raise FileNotFoundError(f"Template not found at {template_dir}")
            
        logger.info(f"Using template from: {template_dir}")
        
        if game_root.exists():
            logger.info(f"Removing existing game directory: {game_root}")
            shutil.rmtree(game_root)
            
        logger.info(f"Copying template to: {game_root}")
        # Use copytree with ignore_dangling_symlinks=True and dirs_exist_ok=True
        shutil.copytree(template_dir, game_root, symlinks=False, 
                       ignore_dangling_symlinks=True, 
                       dirs_exist_ok=True)
        
        # Define and ensure all required paths exist
        paths = {
            'root': game_root,
            'src': game_root / "src",
            'data': game_root / "src" / "data",
            'assets': game_root / "src" / "assets",
            'npcs': game_root / "src" / "assets" / "npcs"
        }
        
        # Create directories if they don't exist
        for path_name, path in paths.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created {path_name} directory at: {path}")
            
        logger.info(f"Successfully created game directories for {game_slug}")
        logger.info(f"Returning paths dictionary: {paths}")
        return paths
        
    except Exception as e:
        logger.error(f"Error in ensure_game_directories: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        raise
