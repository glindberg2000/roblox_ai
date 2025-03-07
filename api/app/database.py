import sqlite3
from contextlib import contextmanager
from pathlib import Path
import json
from .config import SQLITE_DB_PATH
from .paths import get_database_paths
from typing import Optional, Dict, Any, Union, List
from .models import AgentMapping
import logging

__all__ = [
    'get_db',
    'store_player_description',
    'get_player_description',
    'get_npc_context',
    'create_agent_mapping',
    'get_agent_mapping'
]

logger = logging.getLogger("roblox_app")

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

def get_npc_context(npc_id: str) -> Optional[Dict]:
    """Get NPC details from database"""
    # What fields are we selecting?
    print(f"Looking up NPC with ID: {npc_id}")
    with get_db() as db:
        cursor = db.execute("""
            SELECT 
                n.npc_id,
                n.display_name,
                n.system_prompt,
                n.abilities,
                a.description as asset_description,
                a.name as asset_name
            FROM npcs n
            LEFT JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
            WHERE n.npc_id = ?
        """, (npc_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
            
        return {
            "npc_id": result["npc_id"],
            "display_name": result["display_name"],
            "system_prompt": f"""
                {result["system_prompt"]}

My appearance: {result["asset_description"] or f'You are a {result["asset_name"]}'}

- I communicate in short messages that fit naturally in chat bubbles. My responses are concise and match the flow of in-game conversations. I avoid long paragraphs or complex explanations. I use very few emojis - only occasional basic face emojis like :) or :D when it really fits the mood.
            """.strip(),
            "abilities": json.loads(result["abilities"] or "[]"),
            "description": result["asset_description"]
        }

def create_agent_mapping(npc_id: str, participant_id: str, agent_id: str) -> AgentMapping:
    """Create a new agent mapping"""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO npc_agents (npc_id, participant_id, letta_agent_id)
            VALUES (?, ?, ?)
            RETURNING *
        """, (npc_id, participant_id, agent_id))
        result = cursor.fetchone()
        db.commit()
        return AgentMapping(**dict(result))

def get_agent_mapping(npc_id: str, participant_id: str, strict_order: bool = True) -> Optional[AgentMapping]:
    """Get existing NPC agent mapping"""
    with get_db() as db:
        if strict_order:
            # Only get exact match with correct order
            cursor = db.execute("""
                SELECT * FROM npc_agents 
                WHERE npc_id = ? AND participant_id = ?
            """, (npc_id, participant_id))
        else:
            # Check both directions (legacy behavior)
            cursor = db.execute("""
                SELECT * FROM npc_agents 
                WHERE (npc_id = ? AND participant_id = ?) OR
                      (npc_id = ? AND participant_id = ?)
            """, (npc_id, participant_id, participant_id, npc_id))
            results = cursor.fetchall()
            if len(results) > 1:
                logger.warning(f"Found multiple mappings for {npc_id}:{participant_id}!")
                for r in results:
                    logger.warning(f"  {r['npc_id']} -> {r['participant_id']}: {r['letta_agent_id']}")
        
        result = cursor.fetchone()
        return AgentMapping(**dict(result)) if result else None

def debug_list_npcs():
    """Debug function to list all NPCs"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT npc_id, id, display_name, system_prompt 
            FROM npcs
            ORDER BY id
        """)
        results = cursor.fetchall()
        print("\nNPCs in database:")
        for row in results:
            print(f"id: {row['id']}, npc_id: {row['npc_id']}, name: {row['display_name']}")
        return results

def debug_list_agent_mappings():
    """Debug function to list all agent mappings"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM npc_agents
            ORDER BY created_at DESC
            LIMIT 5
        """)
        results = cursor.fetchall()
        print("\nRecent agent mappings:")
        for row in results:
            print(f"npc_id: {row['npc_id']}, participant_id: {row['participant_id']}, agent_id: {row['letta_agent_id']}")
        return results

def debug_show_npc(npc_id: str):
    """Debug function to show NPC data"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM npcs WHERE npc_id = ?
        """, (npc_id,))
        result = cursor.fetchone()
        if result:
            print("\nNPC data:")
            for key in result.keys():
                print(f"{key}: {result[key]}")
        else:
            print(f"No NPC found with ID: {npc_id}")

def store_player_description(
    player_id: str, 
    description: str,
    display_name: str = None
) -> None:
    """Store player description in database."""
    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO player_descriptions 
            (player_id, description, display_name, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (player_id, description, display_name))
        db.commit()

def get_player_description(participant_id: str) -> str:
    """Get stored player description from database"""
    with get_db() as db:
        result = db.execute(
            "SELECT description FROM player_descriptions WHERE player_id = ?",
            (participant_id,)
        ).fetchone()
        return result['description'] if result else ""

def get_player_info(participant_id: str) -> Dict[str, str]:
    """Get full player info from database"""
    with get_db() as db:
        result = db.execute(
            "SELECT description, display_name FROM player_descriptions WHERE player_id = ?",
            (participant_id,)
        ).fetchone()
        return {
            "description": result['description'] if result else "",
            "display_name": result['display_name'] if result else None
        }

def get_location_coordinates(slug: str, game_id: int = 61) -> Optional[Dict]:
    """Get location coordinates from assets table"""
    try:
        with get_db() as db:
            # Match the query from the locations endpoint
            query = """
                SELECT 
                    name,
                    description,
                    position_x,
                    position_y,
                    position_z,
                    slug,
                    location_data
                FROM assets
                WHERE is_location = TRUE
                AND slug = ?
                AND game_id = ?
            """
            
            cursor = db.execute(query, (slug, game_id))
            location = cursor.fetchone()
            
            if location:
                logger.info(f"Found location: {location['name']} at coordinates: {location['position_x']}, {location['position_y']}, {location['position_z']}")
                return {
                    "x": location["position_x"],
                    "y": location["position_y"],
                    "z": location["position_z"]
                }
            
            logger.warning(f"No location found for slug: {slug}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting location coordinates: {str(e)}")
        return None

def get_all_locations(game_id: int = 61) -> List[Dict]:
    """Get all locations with their coordinates and metadata"""
    try:
        with get_db() as db:
            query = """
                SELECT 
                    name,
                    description,
                    position_x,
                    position_y,
                    position_z,
                    slug,
                    location_data
                FROM assets
                WHERE is_location = TRUE
                AND game_id = ?
                AND position_x IS NOT NULL  -- Ensure we have coordinates
                AND position_y IS NOT NULL
                AND position_z IS NOT NULL
            """
            
            cursor = db.execute(query, (game_id,))
            locations = cursor.fetchall()
            
            logger.info(f"Found {len(locations)} locations in database")
            for loc in locations:
                logger.debug(f"Location: {loc['name']}, coordinates: ({loc['position_x']}, {loc['position_y']}, {loc['position_z']})")
            
            return [
                {
                    "name": loc["name"],
                    "description": loc["description"],
                    "coordinates": [loc["position_x"], loc["position_y"], loc["position_z"]],
                    "slug": loc["slug"]
                } for loc in locations
            ]
            
    except Exception as e:
        logger.error(f"Error getting locations: {str(e)}")
        return []

def create_agent_mapping_v3(npc_id: str, agent_id: str) -> AgentMapping:
    """Create a new v3 agent mapping (group chatbot)"""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO npc_agents (npc_id, participant_id, letta_agent_id)
            VALUES (?, 'letta_v3', ?)
            RETURNING *
        """, (npc_id, agent_id))
        result = cursor.fetchone()
        db.commit()
        return AgentMapping(**dict(result))

def get_agent_mapping_v3(npc_id: str) -> Optional[AgentMapping]:
    """Get agent mapping for group chatbot"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM npc_agents 
            WHERE npc_id = ? AND participant_id = 'letta_v3'
            LIMIT 1
        """, (npc_id,))
        result = cursor.fetchone()
        return AgentMapping(**dict(result)) if result else None

# Add to the bottom of the file:
if __name__ == "__main__":
    debug_list_npcs()
    debug_list_agent_mappings()
