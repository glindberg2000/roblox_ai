import json
import sqlite3
import sys
from pathlib import Path

# Add api directory to Python path
api_path = Path(__file__).parent.parent.absolute()
sys.path.append(str(api_path))

from app.config import DB_DIR, SQLITE_DB_PATH
from app.utils import get_database_paths
from app.database import get_db

def migrate_data():
    """Migrate data from JSON files to new database structure"""
    try:
        print("Starting data migration...")
        
        # Get database paths
        db_paths = get_database_paths()
        
        print(f"Loading from paths:")
        print(f"Asset JSON: {db_paths['asset']['json']}")
        print(f"NPC JSON: {db_paths['npc']['json']}")
        
        # Load JSON data
        with open(db_paths['asset']['json'], 'r') as f:
            asset_data = json.load(f)
        with open(db_paths['npc']['json'], 'r') as f:
            npc_data = json.load(f)
            
        print(f"Loaded {len(asset_data.get('assets', []))} assets and {len(npc_data.get('npcs', []))} NPCs")
        
        with get_db() as db:
            # First, ensure we have a default game
            db.execute("""
                INSERT OR IGNORE INTO games (name, slug, description)
                VALUES (?, ?, ?)
            """, ("Game1", "game1", "Default game"))
            db.commit()
            
            # Get game_id
            cursor = db.execute("SELECT id FROM games WHERE slug = ?", ("game1",))
            game_id = cursor.fetchone()["id"]
            
            # Migrate assets
            print("\nMigrating assets...")
            for asset in asset_data.get("assets", []):
                db.execute("""
                    INSERT OR REPLACE INTO assets 
                    (asset_id, name, description, image_url, type, tags, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset["assetId"],
                    asset["name"],
                    asset.get("description", ""),
                    asset.get("imageUrl", ""),
                    asset.get("type", "unknown"),
                    json.dumps(asset.get("tags", [])),
                    game_id
                ))
                print(f"Migrated asset: {asset['name']}")
            
            # Migrate NPCs
            print("\nMigrating NPCs...")
            for npc in npc_data.get("npcs", []):
                db.execute("""
                    INSERT OR REPLACE INTO npcs 
                    (npc_id, asset_id, display_name, model, system_prompt,
                     response_radius, spawn_position, abilities, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    npc["id"],
                    npc["assetId"],
                    npc["displayName"],
                    npc.get("model", ""),
                    npc.get("system_prompt", ""),
                    npc.get("responseRadius", 20),
                    json.dumps(npc.get("spawnPosition", {})),
                    json.dumps(npc.get("abilities", [])),
                    game_id
                ))
                print(f"Migrated NPC: {npc['displayName']}")
            
            db.commit()
            
            # Verify migration
            cursor = db.execute("SELECT COUNT(*) as count FROM assets")
            asset_count = cursor.fetchone()["count"]
            cursor = db.execute("SELECT COUNT(*) as count FROM npcs")
            npc_count = cursor.fetchone()["count"]
            
            print(f"\nMigration complete!")
            print(f"Assets in database: {asset_count}")
            print(f"NPCs in database: {npc_count}")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate_data() 