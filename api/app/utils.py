import json
from pathlib import Path
from typing import Dict, Optional
from .config import get_game_paths
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

def format_npc_as_lua(npc):
    """Format a single NPC entry as Lua table"""
    # Convert spawn position from JSON to Vector3
    spawn_pos = json.loads(npc.get('spawn_position', '{"x": 0, "y": 5, "z": 0}'))
    vector3 = f"Vector3.new({spawn_pos.get('x', 0)}, {spawn_pos.get('y', 5)}, {spawn_pos.get('z', 0)})"
    
    # Convert abilities from JSON string to Lua table
    abilities = json.loads(npc.get('abilities', '[]'))
    abilities_lua = "{\n            " + ",\n            ".join(f'"{ability}"' for ability in abilities) + "\n        }"
    
    # Get model name from asset_id
    model_name = f"{npc['asset_id']}.rbxm"
    
    return f"""    {{
        id = "{npc['npc_id']}",
        displayName = "{npc['display_name']}",
        model = "{model_name}",
        responseRadius = {npc.get('response_radius', 20)},
        assetId = "{npc['asset_id']}",
        spawnPosition = {vector3},
        system_prompt = [[{npc.get('system_prompt', '')}]],
        abilities = {abilities_lua},
        shortTermMemory = {{}},
    }},\n"""

def save_lua_database(file_path, data):
    """Save data as Lua module"""
    if 'npcs' in data:
        lua_content = "return {\n"
        for npc in data['npcs']:
            lua_content += format_npc_as_lua(npc)
        lua_content += "}\n"
        
        with open(file_path, 'w') as f:
            f.write(lua_content)

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
            
            # Generate Lua file
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
            })

def sync_game_files(game_slug: str) -> None:
    """Sync both JSON and Lua files from database"""
    generate_lua_from_db(game_slug, 'asset')
    generate_lua_from_db(game_slug, 'npc')

def ensure_game_directories(game_slug: str) -> Dict[str, Path]:
    """Create and return game directory structure"""
    try:
        # Get base directory from config
        BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        logger.info(f"BASE_DIR: {BASE_DIR}")
        
        # List all directories in games folder to debug
        games_dir = BASE_DIR / "games"
        logger.info(f"Contents of {games_dir}:")
        if games_dir.exists():
            for item in games_dir.iterdir():
                logger.info(f"  - {item.name}")
        else:
            logger.error(f"Games directory not found at: {games_dir}")
        
        game_root = BASE_DIR / "games" / game_slug
        logger.info(f"Game root will be: {game_root}")
        
        # Copy from new template location
        template_dir = BASE_DIR / "games" / "_template"
        logger.info(f"Looking for template at: {template_dir}")
        
        if not template_dir.exists():
            # Try alternate location
            template_dir = BASE_DIR / "api" / "templates" / "game_template"
            logger.info(f"Template not found in games/_template, trying: {template_dir}")
            
        if not template_dir.exists():
            logger.error(f"No template found at either location")
            raise FileNotFoundError(f"No template found at {template_dir}")
            
        logger.info(f"Using template from: {template_dir}")
        
        if game_root.exists():
            logger.info(f"Removing existing game directory: {game_root}")
            shutil.rmtree(game_root)
            
        logger.info(f"Copying template to: {game_root}")
        shutil.copytree(template_dir, game_root)
        
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
        return paths
        
    except Exception as e:
        logger.error(f"Error in ensure_game_directories: {str(e)}")
        logger.error(f"Stack trace:", exc_info=True)
        raise
