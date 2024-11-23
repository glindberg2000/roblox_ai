import sqlite3
from contextlib import contextmanager
from pathlib import Path
import json
from .config import SQLITE_DB_PATH
from .paths import get_database_paths

@contextmanager
def get_db():
    db = sqlite3.connect(SQLITE_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def generate_lua_from_db(game_slug: str, db_type: str) -> None:
    """Generate Lua file directly from database data"""
    with get_db() as db:
        db.row_factory = sqlite3.Row
        
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        if db_type == 'asset':
            # Get assets from database
            cursor = db.execute("""
                SELECT asset_id, name, description, type, tags, image_url
                FROM assets WHERE game_id = ?
            """, (game_id,))
            assets = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file
            save_lua_database(db_paths['asset']['lua'], {
                "assets": [{
                    "assetId": asset["asset_id"],
                    "name": asset["name"],
                    "description": asset.get("description", ""),
                    "type": asset.get("type", "unknown"),
                    "imageUrl": asset.get("image_url", ""),
                    "tags": json.loads(asset.get("tags", "[]"))
                } for asset in assets]
            })
            
        elif db_type == 'npc':
            # Get NPCs from database
            cursor = db.execute("""
                SELECT npc_id, display_name, asset_id, model, system_prompt,
                       response_radius, spawn_position, abilities
                FROM npcs WHERE game_id = ?
            """, (game_id,))
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file
            save_lua_database(db_paths['npc']['lua'], {
                "npcs": [{
                    "id": npc["npc_id"],
                    "displayName": npc["display_name"],
                    "assetId": npc["asset_id"],
                    "model": npc.get("model", ""),
                    "system_prompt": npc.get("system_prompt", ""),
                    "responseRadius": npc.get("response_radius", 20),
                    "spawnPosition": json.loads(npc.get("spawn_position", "{}")),
                    "abilities": json.loads(npc.get("abilities", "[]")),
                    "shortTermMemory": []
                } for npc in npcs]
            })

def init_db():
    """Initialize the database with schema"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    with get_db() as db:
        # Create tables if they don't exist
        db.executescript("""
            -- Games table
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Assets table
            CREATE TABLE IF NOT EXISTS assets (
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
            CREATE TABLE IF NOT EXISTS npcs (
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
        
        # Ensure game1 exists
        db.execute("""
            INSERT OR IGNORE INTO games (title, slug, description)
            VALUES ('Game 1', 'game1', 'The default game instance')
            ON CONFLICT(slug) DO UPDATE SET
            title = 'Game 1',
            description = 'The default game instance'
        """)
        
        db.commit()

def import_json_to_db(game_slug: str, json_dir: Path) -> None:
    """Import JSON data into database"""
    with get_db() as db:
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
        game_id = game['id']
        
        # Import assets
        asset_file = json_dir / 'AssetDatabase.json'
        if asset_file.exists():
            with open(asset_file, 'r') as f:
                asset_data = json.load(f)
                for asset in asset_data.get('assets', []):
                    db.execute("""
                        INSERT OR REPLACE INTO assets 
                        (asset_id, name, description, type, tags, image_url, game_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        asset['assetId'],
                        asset['name'],
                        asset.get('description', ''),
                        asset.get('type', 'unknown'),
                        json.dumps(asset.get('tags', [])),
                        asset.get('imageUrl', ''),
                        game_id
                    ))
        
        # Import NPCs
        npc_file = json_dir / 'NPCDatabase.json'
        if npc_file.exists():
            with open(npc_file, 'r') as f:
                npc_data = json.load(f)
                for npc in npc_data.get('npcs', []):
                    db.execute("""
                        INSERT OR REPLACE INTO npcs 
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
                        game_id
                    ))
        
        db.commit()

def check_db_state():
    """Check database tables and their contents"""
    with get_db() as db:
        print("\n=== Database State ===")
        
        # Check tables
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name;
        """)
        tables = cursor.fetchall()
        print("Tables:", [table[0] for table in tables])
        
        # Check games
        cursor = db.execute("SELECT * FROM games")
        games = cursor.fetchall()
        print("\nGames in database:")
        for game in games:
            print(f"- {game['title']} (ID: {game['id']}, slug: {game['slug']})")
            
            # Count assets and NPCs for this game
            assets = db.execute("""
                SELECT COUNT(*) as count FROM assets WHERE game_id = ?
            """, (game['id'],)).fetchone()['count']
            
            npcs = db.execute("""
                SELECT COUNT(*) as count FROM npcs WHERE game_id = ?
            """, (game['id'],)).fetchone()['count']
            
            print(f"  Assets: {assets}")
            print(f"  NPCs: {npcs}")
            
            # Show asset details
            print("\n  Assets:")
            cursor = db.execute("SELECT * FROM assets WHERE game_id = ?", (game['id'],))
            for asset in cursor.fetchall():
                print(f"    - {asset['name']} (ID: {asset['asset_id']})")
            
            # Show NPC details
            print("\n  NPCs:")
            cursor = db.execute("SELECT * FROM npcs WHERE game_id = ?", (game['id'],))
            for npc in cursor.fetchall():
                print(f"    - {npc['display_name']} (ID: {npc['npc_id']})")
        
        print("=====================\n")

def migrate_existing_data():
    """Migrate existing JSON data to SQLite if needed"""
    with get_db() as db:
        # Get the default game
        cursor = db.execute("SELECT id FROM games WHERE slug = 'game1'")
        game = cursor.fetchone()
        if not game:
            print("Error: Default game not found")
            return
            
        default_game_id = game['id']
        
        # Load existing JSON data from the correct paths
        db_paths = get_database_paths("game1")
        
        try:
            # Load JSON data
            with open(db_paths['asset']['json'], 'r') as f:
                asset_data = json.load(f)
            with open(db_paths['npc']['json'], 'r') as f:
                npc_data = json.load(f)
            
            print(f"Found {len(asset_data.get('assets', []))} assets and {len(npc_data.get('npcs', []))} NPCs to migrate")
            
            # Migrate assets
            for asset in asset_data.get('assets', []):
                db.execute("""
                    INSERT OR REPLACE INTO assets 
                    (asset_id, name, description, type, tags, image_url, game_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset['assetId'],
                    asset['name'],
                    asset.get('description', ''),
                    asset.get('type', 'unknown'),
                    json.dumps(asset.get('tags', [])),
                    asset.get('imageUrl', ''),
                    default_game_id
                ))
            
            # Migrate NPCs
            for npc in npc_data.get('npcs', []):
                db.execute("""
                    INSERT OR REPLACE INTO npcs 
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
