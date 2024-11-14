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
        
        # Initialize the database first
        init_db()
        
        # Get database paths
        db_paths = get_database_paths()
        
        # Load JSON data
        asset_data = load_json_database(db_paths['asset']['json'])
        
        # Connect to SQLite
        with get_db() as db:
            # First, count existing items
            cursor = db.execute("SELECT COUNT(*) as count FROM items")
            before_count = cursor.fetchone()["count"]
            print(f"Items in database before migration: {before_count}")
            
            # Migrate assets
            for asset in asset_data.get("assets", []):
                # Prepare properties JSON
                properties = {
                    "imageUrl": asset.get("imageUrl", ""),
                    "storage_type": asset.get("storage_type", "")
                }
                
                # Insert into SQLite, using REPLACE to handle duplicates
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
            
            db.commit()
            
            # Verify migration
            cursor = db.execute("SELECT COUNT(*) as count FROM items")
            after_count = cursor.fetchone()["count"]
            print(f"Migration completed successfully!")
            print(f"Items in database after migration: {after_count}")
            print(f"Added {after_count - before_count} new items")
            
            # Print some sample data
            cursor = db.execute("SELECT * FROM items LIMIT 3")
            samples = cursor.fetchall()
            print("\nSample items:")
            for sample in samples:
                print(f"- {dict(sample)['name']} (ID: {dict(sample)['item_id']})")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate_json_to_sqlite() 