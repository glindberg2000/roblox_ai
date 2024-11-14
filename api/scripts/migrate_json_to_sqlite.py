import json
import sys
import os
from pathlib import Path

# Add the api directory to Python path
api_path = Path(__file__).parent.parent
sys.path.append(str(api_path))

from app.database import get_db, init_db
from app.utils import load_json_database, get_database_paths

def migrate_json_to_sqlite():
    """Migrate data from JSON files to SQLite database"""
    try:
        print("Starting migration from JSON to SQLite...")
        init_db()
        
        db_paths = get_database_paths()
        
        # Load both asset and NPC data
        asset_data = load_json_database(db_paths['asset']['json'])
        npc_data = load_json_database(db_paths['npc']['json'])
        
        print("Asset data sample:", list(asset_data.get("assets", []))[:1])
        print("NPC data sample:", list(npc_data.get("npcs", []))[:1])
        
        with get_db() as db:
            # First clear existing data
            db.execute("DELETE FROM items")
            
            # Migrate assets
            for asset in asset_data.get("assets", []):
                properties = {
                    "imageUrl": asset.get("imageUrl", ""),
                    "storage_type": "assets"  # Mark as asset
                }
                
                db.execute("""
                    INSERT OR REPLACE INTO items 
                    (item_id, name, description, properties)
                    VALUES (?, ?, ?, ?)
                """, (
                    asset["assetId"],
                    asset["name"],
                    asset.get("description", ""),
                    json.dumps(properties)
                ))
            
            # Migrate NPCs with error handling
            for npc in npc_data.get("npcs", []):
                try:
                    properties = {
                        "imageUrl": npc.get("imageUrl", ""),
                        "storage_type": "npcs",
                        "displayName": npc.get("displayName", "Unknown NPC"),
                        "model": npc.get("model", ""),
                        "abilities": npc.get("abilities", []),
                        "responseRadius": npc.get("responseRadius", 20),
                        "spawnPosition": npc.get("spawnPosition", {}),
                        "id": npc.get("id", ""),  # Add NPC ID
                        "shortTermMemory": npc.get("shortTermMemory", [])  # Add memory
                    }
                    
                    print(f"Processing NPC: {npc}")
                    
                    db.execute("""
                        INSERT OR REPLACE INTO items 
                        (item_id, name, description, properties)
                        VALUES (?, ?, ?, ?)
                    """, (
                        npc["assetId"],
                        npc.get("displayName", "Unknown NPC"),  # Use displayName as name
                        npc.get("system_prompt", ""),  # Store system_prompt in description
                        json.dumps(properties)
                    ))
                except Exception as e:
                    print(f"Error processing NPC: {npc}")
                    print(f"Error: {e}")
                    continue
            
            db.commit()
            
            # Verify migration
            cursor = db.execute("SELECT COUNT(*) as count FROM items")
            total = cursor.fetchone()["count"]
            
            cursor = db.execute("""
                SELECT COUNT(*) as count 
                FROM items 
                WHERE json_extract(properties, '$.storage_type') = 'npcs'
            """)
            npc_count = cursor.fetchone()["count"]
            
            cursor = db.execute("""
                SELECT COUNT(*) as count 
                FROM items 
                WHERE json_extract(properties, '$.storage_type') = 'assets'
            """)
            asset_count = cursor.fetchone()["count"]
            
            print(f"Migration completed successfully!")
            print(f"Total items: {total}")
            print(f"Assets: {asset_count}")
            print(f"NPCs: {npc_count}")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate_json_to_sqlite() 