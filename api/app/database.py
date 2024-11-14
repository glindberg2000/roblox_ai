import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import DB_DIR, SQLITE_DB_PATH
import json

@contextmanager
def get_db():
    db = sqlite3.connect(SQLITE_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database with schema"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    with get_db() as db:
        # Create schema
        schema_path = DB_DIR / 'schema.sql'
        with open(schema_path, 'r') as f:
            db.executescript(f.read())
        
        # Create default game if it doesn't exist
        db.execute("""
            INSERT OR IGNORE INTO games (name, slug, description)
            VALUES (?, ?, ?)
        """, ("Game1", "game1", "Default game"))
        db.commit()

def get_items(game_id=None):
    """Get all items (assets and NPCs)"""
    with get_db() as db:
        if game_id:
            # Get assets
            cursor = db.execute("""
                SELECT asset_id as item_id, name, description, image_url, type, tags
                FROM assets WHERE game_id = ?
            """, (game_id,))
            assets = cursor.fetchall()
            
            # Get NPCs
            cursor = db.execute("""
                SELECT n.asset_id as item_id, n.display_name as name, 
                       n.system_prompt as description, a.image_url,
                       'npc' as type, n.abilities as tags
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.game_id = ?
            """, (game_id,))
            npcs = cursor.fetchall()
        else:
            # Get all assets
            cursor = db.execute("""
                SELECT asset_id as item_id, name, description, image_url, type, tags
                FROM assets
            """)
            assets = cursor.fetchall()
            
            # Get all NPCs
            cursor = db.execute("""
                SELECT n.asset_id as item_id, n.display_name as name, 
                       n.system_prompt as description, a.image_url,
                       'npc' as type, n.abilities as tags
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
            """)
            npcs = cursor.fetchall()
        
        # Convert rows to dicts and combine results
        return [dict(row) for row in assets] + [dict(row) for row in npcs]

def get_npcs(game_id=None):
    """Get all NPCs"""
    with get_db() as db:
        if game_id:
            cursor = db.execute("""
                SELECT n.*, a.image_url
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.game_id = ?
            """, (game_id,))
        else:
            cursor = db.execute("""
                SELECT n.*, a.image_url
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
            """)
        return [dict(row) for row in cursor.fetchall()]
