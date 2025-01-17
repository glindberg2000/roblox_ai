import os
import sys
from pathlib import Path

# Get absolute path to api directory
api_path = str(Path(__file__).resolve().parent.parent.absolute())

# Add to Python path if not already there
if api_path not in sys.path:
    sys.path.insert(0, api_path)

print(f"API path: {api_path}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from app.database import init_db
    from app.utils import load_json_database, get_database_paths
    import json

    def setup_database():
        """Initialize database and migrate data"""
        try:
            print("Initializing database...")
            init_db()
            
            print("Loading JSON data...")
            db_paths = get_database_paths()
            asset_data = load_json_database(db_paths['asset']['json'])
            
            print("Migrating data to SQLite...")
            from app.database import get_db
            with get_db() as db:
                # First, count existing items
                cursor = db.execute("SELECT COUNT(*) as count FROM items")
                before_count = cursor.fetchone()["count"]
                print(f"Items in database before migration: {before_count}")
                
                # Migrate assets
                for asset in asset_data.get("assets", []):
                    properties = {
                        "imageUrl": asset.get("imageUrl", ""),
                        "storage_type": asset.get("storage_type", "")
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
                
                db.commit()
                
                # Verify migration
                cursor = db.execute("SELECT COUNT(*) as count FROM items")
                after_count = cursor.fetchone()["count"]
                print(f"Migration completed successfully!")
                print(f"Items in database after migration: {after_count}")
                print(f"Added {after_count - before_count} new items")
                
        except Exception as e:
            print(f"Error during setup: {e}")
            raise

    if __name__ == "__main__":
        setup_database()

except ImportError as e:
    print(f"Import error: {e}")
    print(f"Make sure you're running this script from the project root directory")
    sys.exit(1) 