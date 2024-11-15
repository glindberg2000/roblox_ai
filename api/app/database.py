import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import DB_DIR, SQLITE_DB_PATH
import json
import os
from .utils import get_database_paths, load_json_database

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
        # Drop any temporary tables first
        db.execute("DROP TABLE IF EXISTS games_new")
        
        # Drop existing tables in correct order
        db.executescript("""
            DROP TABLE IF EXISTS npcs;
            DROP TABLE IF EXISTS assets;
            DROP TABLE IF EXISTS games;
        """)
        
        # Create tables with new schema
        db.executescript("""
            -- Games table
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Assets table
            CREATE TABLE assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                type TEXT,
                tags TEXT,  -- JSON array
                game_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                UNIQUE(asset_id, game_id)
            );

            -- NPCs table
            CREATE TABLE npcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npc_id TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                model TEXT,
                system_prompt TEXT,
                response_radius INTEGER DEFAULT 20,
                spawn_position TEXT,  -- JSON object
                abilities TEXT,  -- JSON array
                game_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            );
        """)
        
        # Create default game
        db.execute("""
            INSERT INTO games (title, slug, description)
            VALUES (?, ?, ?)
        """, ('Default Game', 'default-game', 'The default game instance'))
        
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

def check_db_state():
    """Check database tables and their contents"""
    with get_db() as db:
        # Check tables
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name;
        """)
        tables = cursor.fetchall()
        print("\n=== Database State ===")
        print("Tables:", [table[0] for table in tables])
        
        # Check games
        cursor = db.execute("SELECT * FROM games")
        games = cursor.fetchall()
        print("\nGames in database:")
        for game in games:
            print(f"- {game['title']} (ID: {game['id']}, slug: {game['slug']})")
            
            # Count assets and NPCs for this game
            assets = db.execute("SELECT COUNT(*) as count FROM assets WHERE game_id = ?", 
                              (game['id'],)).fetchone()['count']
            npcs = db.execute("SELECT COUNT(*) as count FROM npcs WHERE game_id = ?", 
                            (game['id'],)).fetchone()['count']
            print(f"  Assets: {assets}, NPCs: {npcs}")
        print("=====================\n")

def migrate_existing_data():
    """Migrate existing JSON data to SQLite if needed"""
    with get_db() as db:
        # Get the default game
        default_game = db.execute("""
            SELECT id FROM games WHERE slug = 'default-game'
        """).fetchone()
        
        if not default_game:
            print("Error: Default game not found")
            return
            
        default_game_id = default_game['id']
        
        # Load existing JSON data from the correct paths
        db_paths = get_database_paths()
        
        # Debug output
        print(f"Migrating data from:")
        print(f"Assets: {db_paths['asset']['json']}")
        print(f"NPCs: {db_paths['npc']['json']}")
        
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

def fetch_all_games():
    """Fetch all games from the database"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id, title, slug, description 
            FROM games 
            ORDER BY title
        """)
        return [dict(row) for row in cursor.fetchall()]

def create_game(title: str, slug: str, description: str):
    """Create a new game entry"""
    with get_db() as db:
        try:
            cursor = db.execute("""
                INSERT INTO games (title, slug, description)
                VALUES (?, ?, ?)
                RETURNING id
            """, (title, slug, description))
            result = cursor.fetchone()
            db.commit()
            return result['id']
        except Exception as e:
            db.rollback()
            raise e

def fetch_game(slug: str):
    """Fetch a single game by slug"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id, title, slug, description 
            FROM games 
            WHERE slug = ?
        """, (slug,))
        result = cursor.fetchone()
        return dict(result) if result else None

def update_game(slug: str, title: str, description: str):
    """Update a game's details"""
    with get_db() as db:
        try:
            db.execute("""
                UPDATE games 
                SET title = ?, description = ?
                WHERE slug = ?
            """, (title, description, slug))
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

def delete_game(slug: str):
    """Delete a game and its associated assets and NPCs"""
    with get_db() as db:
        try:
            # Get game ID first
            cursor = db.execute("SELECT id FROM games WHERE slug = ?", (slug,))
            game = cursor.fetchone()
            if not game:
                raise ValueError("Game not found")
                
            game_id = game['id']
            
            # Delete associated NPCs first (due to foreign key constraints)
            db.execute("DELETE FROM npcs WHERE game_id = ?", (game_id,))
            
            # Delete associated assets
            db.execute("DELETE FROM assets WHERE game_id = ?", (game_id,))
            
            # Finally delete the game
            db.execute("DELETE FROM games WHERE id = ?", (game_id,))
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

def count_assets(game_id: int):
    """Count assets for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT COUNT(*) as count 
            FROM assets 
            WHERE game_id = ?
        """, (game_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0

def count_npcs(game_id: int):
    """Count NPCs for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT COUNT(*) as count 
            FROM npcs 
            WHERE game_id = ?
        """, (game_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0

def fetch_assets_by_game(game_id: int):
    """Fetch assets for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM assets 
            WHERE game_id = ?
            ORDER BY name
        """, (game_id,))
        return [dict(row) for row in cursor.fetchall()]

def fetch_npcs_by_game(game_id: int):
    """Fetch NPCs for a specific game"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT n.*, a.image_url
            FROM npcs n
            JOIN assets a ON n.asset_id = a.asset_id
            WHERE n.game_id = ?
            ORDER BY n.display_name
        """, (game_id,))
        return [dict(row) for row in cursor.fetchall()]

def fetch_all_assets():
    """Fetch all assets"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM assets
            ORDER BY name
        """)
        return [dict(row) for row in cursor.fetchall()]

def fetch_all_npcs():
    """Fetch all NPCs"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT n.*, a.image_url
            FROM npcs n
            JOIN assets a ON n.asset_id = a.asset_id
            ORDER BY n.display_name
        """)
        return [dict(row) for row in cursor.fetchall()]
