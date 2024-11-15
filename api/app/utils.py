import json
from pathlib import Path
from typing import Dict, Optional
from .config import get_game_paths
import os

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

def save_lua_database(path, data):
    """Save data as a Lua table"""
    try:
        with open(path, 'w') as f:
            f.write("return {\n")
            
            # Write assets if present
            if "assets" in data:
                for asset in data.get("assets", []):
                    f.write("    {\n")
                    f.write(f'        assetId = "{asset["assetId"]}",\n')
                    f.write(f'        name = "{asset["name"]}",\n')
                    f.write(f'        description = "{asset.get("description", "")}",\n')
                    f.write("    },\n")
            
            # Write NPCs if present
            if "npcs" in data:
                for npc in data.get("npcs", []):
                    f.write("    {\n")
                    f.write(f'        id = "{npc.get("id", "")}",\n')
                    f.write(f'        displayName = "{npc.get("displayName", "Unknown NPC")}",\n')
                    f.write(f'        model = "{npc.get("model", "")}",\n')
                    f.write(f'        responseRadius = {npc.get("responseRadius", 20)},\n')
                    f.write(f'        assetId = "{npc["assetId"]}",\n')
                    
                    # Handle spawnPosition using Vector3.new()
                    spawn = npc.get("spawnPosition", {})
                    f.write(f'        spawnPosition = Vector3.new({spawn.get("x", 0)}, {spawn.get("y", 0)}, {spawn.get("z", 0)}),\n')
                    
                    # Handle system prompt with [[ ]] for multi-line strings
                    f.write(f'        system_prompt = [[{npc.get("system_prompt", "")}]],\n')
                    
                    # Handle abilities
                    f.write('        abilities = {\n')
                    for ability in npc.get("abilities", []):
                        f.write(f'            "{ability}",\n')
                    f.write('        },\n')
                    
                    # Add shortTermMemory
                    f.write('        shortTermMemory = {},\n')
                    
                    f.write("    },\n")
            
            f.write("}\n")
    except Exception as e:
        print(f"Error saving Lua database to {path}: {e}")
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
