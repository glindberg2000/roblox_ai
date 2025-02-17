import sqlite3
import json
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from api.config import DB_DIR, SQLITE_DB_PATH
from api.utils import get_database_paths, load_json_database
from api.db.migrations import run_migrations

def init_db():
    """Initialize the database with schema"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run all migrations
    run_migrations()

def migrate_existing_data():
    """Migrate existing JSON data to SQLite"""
    with sqlite3.connect(SQLITE_DB_PATH) as db:
        # Get the default game
        cursor = db.execute("SELECT id FROM games WHERE slug = 'default-game'")
        default_game = cursor.fetchone()
        
        if not default_game:
            print("Error: Default game not found")
            return
            
        default_game_id = default_game[0]
        
        # Load existing JSON data
        db_paths = get_database_paths()
        
        try:
            # Migrate assets
            asset_data = load_json_database(db_paths['asset']['json'])
            print(f"Found {len(asset_data.get('assets', []))} assets to migrate")
            
            for asset in asset_data.get('assets', []):
                db.execute("""
                    INSERT OR IGNORE INTO assets 
                    (asset_id, name, description, image_url, type, tags, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset['assetId'],
                    asset['name'],
                    asset.get('description', ''),
                    asset.get('imageUrl', ''),
                    asset.get('type', 'unknown'),
                    json.dumps(asset.get('tags', [])),
                    default_game_id
                ))
                print(f"Migrated asset: {asset['name']}")
            
            # Migrate NPCs
            npc_data = load_json_database(db_paths['npc']['json'])
            print(f"Found {len(npc_data.get('npcs', []))} NPCs to migrate")
            
            for npc in npc_data.get('npcs', []):
                db.execute("""
                    INSERT OR IGNORE INTO npcs 
                    (npc_id, display_name, asset_id, model, system_prompt, 
                     response_radius, spawn_position, abilities, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    npc['id'],
                    npc['displayName'],
                    npc['assetId'],
                    npc.get('model', ''),
                    npc.get('system_prompt', ''),
                    npc.get('responseRadius', 20),
                    json.dumps(npc.get('spawnPosition', {})),
                    json.dumps(npc.get('abilities', [])),
                    default_game_id
                ))
                print(f"Migrated NPC: {npc['displayName']}")
            
            db.commit()
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.rollback()
            raise 