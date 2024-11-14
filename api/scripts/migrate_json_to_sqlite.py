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
        
        with get_db() as db:
            # Create default game
            db.execute("""
                INSERT OR IGNORE INTO games (name, slug, description)
                VALUES (?, ?, ?)
            """, ("Game1", "game1", "Default game"))
            db.commit()
            
            # Get the game_id
            cursor = db.execute("SELECT id FROM games WHERE slug = ?", ("game1",))
            game_id = cursor.fetchone()["id"]
            
            db_paths = get_database_paths()
            
            # Load both asset and NPC data
            print("Loading databases...")
            asset_data = load_json_database(db_paths['asset']['json'])
            npc_data = load_json_database(db_paths['npc']['json'])
            
            # First clear existing data
            db.execute("DELETE FROM items")
            
            # Track all assets and NPCs
            processed_asset_ids = set()
            
            # First, migrate ALL assets from asset database
            print("\nMigrating all assets from AssetDatabase...")
            for asset in asset_data.get("assets", []):
                asset_id = asset["assetId"]
                properties = {
                    "imageUrl": asset.get("imageUrl", ""),
                    "storage_type": "assets",
                    "type": asset.get("type", ""),
                    "tags": asset.get("tags", [])
                }
                
                # For NPC base assets, add NPC-specific properties
                is_npc_asset = any(npc["assetId"] == asset_id for npc in npc_data.get("npcs", []))
                if is_npc_asset:
                    properties["type"] = "npc_base"
                    if "tags" not in properties:
                        properties["tags"] = []
                    properties["tags"].append("npc")
                
                db.execute("""
                    INSERT OR REPLACE INTO items 
                    (item_id, name, description, properties, game_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    asset_id,
                    asset["name"],
                    asset.get("description", ""),
                    json.dumps(properties),
                    game_id
                ))
                processed_asset_ids.add(asset_id)
                print(f"Processed asset: {asset_id} - {asset['name']}")
            
            # Then migrate NPCs, using npc_ prefix for item_id
            print("\nMigrating NPCs...")
            npc_count = 0
            for npc in npc_data.get("npcs", []):
                try:
                    asset_id = npc["assetId"]
                    
                    # Verify the asset exists
                    if asset_id not in processed_asset_ids:
                        print(f"Warning: NPC {npc.get('displayName')} references missing asset {asset_id}")
                        continue
                    
                    npc_properties = {
                        "imageUrl": npc.get("imageUrl", ""),
                        "storage_type": "npcs",
                        "displayName": npc.get("displayName", "Unknown NPC"),
                        "model": npc.get("model", ""),
                        "abilities": npc.get("abilities", []),
                        "responseRadius": npc.get("responseRadius", 20),
                        "spawnPosition": npc.get("spawnPosition", {}),
                        "id": npc.get("id", ""),
                        "shortTermMemory": npc.get("shortTermMemory", []),
                        "base_asset_id": asset_id  # Link to the base asset
                    }
                    
                    db.execute("""
                        INSERT OR REPLACE INTO items 
                        (item_id, name, description, properties, game_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        f"npc_{asset_id}",  # Use prefix for NPC entries
                        npc.get("displayName", "Unknown NPC"),
                        npc.get("system_prompt", ""),
                        json.dumps(npc_properties),
                        game_id
                    ))
                    npc_count += 1
                    print(f"Processed NPC: {npc.get('displayName')} with asset {asset_id}")
                    
                except Exception as e:
                    print(f"Error processing NPC: {npc}")
                    print(f"Error: {e}")
                    continue
            
            db.commit()
            
            # Print statistics
            cursor = db.execute("SELECT COUNT(*) as count FROM items WHERE json_extract(properties, '$.storage_type') = 'assets'")
            asset_count = cursor.fetchone()["count"]
            
            cursor = db.execute("SELECT COUNT(*) as count FROM items WHERE json_extract(properties, '$.storage_type') = 'npcs'")
            npc_count = cursor.fetchone()["count"]
            
            print(f"\nMigration completed successfully!")
            print(f"Total assets in AssetDatabase: {len(asset_data.get('assets', []))}")
            print(f"Assets imported: {asset_count}")
            print(f"NPCs imported: {npc_count}")
            
            # Print all assets for verification
            print("\nAll imported assets:")
            cursor = db.execute("SELECT item_id, name FROM items WHERE json_extract(properties, '$.storage_type') = 'assets'")
            for row in cursor.fetchall():
                print(f"Asset: {row['item_id']} - {row['name']}")
            
            print("\nAll imported NPCs:")
            cursor = db.execute("""
                SELECT i.item_id, i.name, json_extract(i.properties, '$.base_asset_id') as base_asset
                FROM items i
                WHERE json_extract(i.properties, '$.storage_type') = 'npcs'
            """)
            for row in cursor.fetchall():
                print(f"NPC: {row['item_id']} - {row['name']} (Base Asset: {row['base_asset']})")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate_json_to_sqlite() 