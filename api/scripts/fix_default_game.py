import sqlite3
from pathlib import Path
import json
from api.app.config import SQLITE_DB_PATH, ensure_game_directories
from api.app.utils import get_database_paths, save_json_database, save_lua_database

def fix_default_game():
    """Fix default game data and ensure all assets/NPCs are properly associated"""
    with sqlite3.connect(SQLITE_DB_PATH) as db:
        db.row_factory = sqlite3.Row
        
        # Get or create default game with slug 'game1'
        cursor = db.execute("""
            INSERT OR IGNORE INTO games (title, slug, description)
            VALUES ('Game 1', 'game1', 'The default game instance')
        """)
        db.commit()
        
        # Get the default game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = 'game1'")
        game = cursor.fetchone()
        
        if not game:
            raise Exception("Failed to create or find default game")
            
        default_game_id = game['id']
        print(f"Default game ID: {default_game_id}")
        
        # Get current data from database
        cursor = db.execute("""
            SELECT asset_id, name, description, type, tags, image_url
            FROM assets 
            WHERE game_id = ?
        """, (default_game_id,))
        assets = [dict(row) for row in cursor.fetchall()]
        
        cursor = db.execute("""
            SELECT npc_id as id, display_name as displayName, asset_id as assetId,
                   model, system_prompt, response_radius as responseRadius,
                   spawn_position as spawnPosition, abilities
            FROM npcs 
            WHERE game_id = ?
        """, (default_game_id,))
        npcs = [dict(row) for row in cursor.fetchall()]
        
        print(f"Found {len(assets)} assets and {len(npcs)} NPCs in database")
        
        # Format the data
        asset_data = {"assets": [
            {
                "assetId": asset["asset_id"],
                "name": asset["name"],
                "description": asset["description"],
                "type": asset["type"],
                "imageUrl": asset["image_url"],
                "tags": json.loads(asset["tags"]) if asset["tags"] else []
            } for asset in assets
        ]}
        
        npc_data = {"npcs": [
            {
                "id": npc["id"],
                "displayName": npc["displayName"],
                "assetId": npc["assetId"],
                "model": npc["model"],
                "system_prompt": npc["system_prompt"],
                "responseRadius": npc["responseRadius"],
                "spawnPosition": json.loads(npc["spawnPosition"]) if npc["spawnPosition"] else {"x": 0, "y": 5, "z": 0},
                "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                "shortTermMemory": []
            } for npc in npcs
        ]}
        
        # Get paths
        db_paths = get_database_paths("game1")
        
        # Save asset files
        save_json_database(db_paths['asset']['json'], asset_data)
        save_lua_database(db_paths['asset']['lua'], {"assets": asset_data["assets"]})
        
        # Save NPC files
        save_json_database(db_paths['npc']['json'], npc_data)
        save_lua_database(db_paths['npc']['lua'], {"npcs": npc_data["npcs"]})
        
        print(f"Default game now has {len(assets)} assets and {len(npcs)} NPCs")
        print("Database and file system synchronized successfully")

if __name__ == "__main__":
    fix_default_game() 