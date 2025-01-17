#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path

# Get absolute path to api directory
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    
    # Import our modules
    from app.database import init_db, get_db
    from app.utils import load_json_database, get_database_paths
    
    print("Successfully imported modules")
    print("Initializing database...")
    init_db()
    
    print("Loading JSON data...")
    db_paths = get_database_paths()
    asset_data = load_json_database(db_paths['asset']['json'])
    
    print("Migrating data to SQLite...")
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

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the api directory")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1) 