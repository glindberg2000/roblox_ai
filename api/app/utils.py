import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional
from .config import get_game_paths, BASE_DIR, GAMES_DIR
from .db import get_db
import os
import shutil
import logging
from .paths import get_database_paths
from .models import HumanContextData

# Set up logger
logger = logging.getLogger("roblox_app")

def load_json_database(path: Path) -> dict:
    """Load a JSON database file"""
    try:
        if not path.exists():
            return {"assets": [], "npcs": []}
            
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON database from {path}: {e}")
        return {"assets": [], "npcs": []}

def save_json_database(path: Path, data: dict) -> None:
    """Save data to a JSON database file"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON database to {path}: {e}")
        raise

def format_npc_as_lua(npc: dict, db=None) -> str:
    """Format a single NPC as Lua code"""
    try:
        # Handle abilities - could be string or list
        abilities_raw = npc.get('abilities', '[]')
        if isinstance(abilities_raw, list):
            abilities = abilities_raw  # Already a list
        else:
            abilities = json.loads(abilities_raw)  # Parse JSON string
            
        # Format abilities as Lua table with proper indentation
        abilities_lua = "{\n" + "".join(f'            "{ability}", \n' for ability in abilities) + "        }"
            
        # Use new coordinate columns directly
        vector3 = f"Vector3.new({npc['spawn_x']}, {npc['spawn_y']}, {npc['spawn_z']})"

        # Use the assetId as the model name
        model = npc['asset_id']
        display_name = npc['display_name']
            
        return (f"        {{\n"
                f"            id = \"{npc['npc_id']}\", \n"
                f"            displayName = \"{display_name}\", \n"
                f"            name = \"{display_name}\", \n"
                f"            assetId = \"{model}\", \n"
                f"            model = \"{model}\", \n"
                f"            modelName = \"{display_name}\", \n"
                f"            responseRadius = {npc.get('response_radius', 20)}, \n"
                f"            spawnPosition = {vector3}, \n"
                f"            abilities = {abilities_lua}, \n"
                f"            shortTermMemory = {{}}, \n"
                f"        }},")
    except Exception as e:
        logger.error(f"Error formatting NPC as Lua: {e}")
        logger.error(f"NPC data: {npc}")
        raise

def format_asset_as_lua(asset: dict) -> str:
    """Format single asset as Lua table entry with location data"""
    # Escape any quotes in strings
    description = asset['description'].replace('"', '\\"') if asset.get('description') else ""
    name = asset['name'].replace('"', '\\"')
    slug = asset.get('slug', '')
    
    # Parse JSON fields
    location_data = {}
    if asset.get('location_data'):
        try:
            location_data = json.loads(asset['location_data']) if isinstance(asset['location_data'], str) else asset['location_data']
        except:
            location_data = {}
            
    aliases = []
    if asset.get('aliases'):
        try:
            aliases = json.loads(asset['aliases']) if isinstance(asset['aliases'], str) else asset['aliases']
        except:
            aliases = []

    # Format location data
    location_info = ""
    if asset.get('is_location'):
        location_info = f"""
            isLocation = true,
            position = Vector3.new({asset.get('position_x', 0)}, {asset.get('position_y', 0)}, {asset.get('position_z', 0)}),
            locationData = {{
                area = "{location_data.get('area', 'unknown')}",
                type = "{location_data.get('type', 'unknown')}",
                owner = "{location_data.get('owner', '')}",
                interactable = {str(location_data.get('interactable', False)).lower()},
                tags = {{{', '.join(f'"{tag}"' for tag in location_data.get('tags', []))}}}
            }},
            aliases = {{{', '.join(f'"{alias}"' for alias in aliases)}}},"""

    return f"""        {{
            assetId = "{asset['asset_id']}",
            name = "{name}",
            slug = "{slug}",
            description = "{description}",
            type = "{asset.get('type', 'Model')}",{location_info}
        }},\n"""

def save_lua_database(game_slug: str, db: sqlite3.Connection) -> None:
    """Save both NPC and Asset Lua databases for a game"""
    try:
        # Get game ID
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
            
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        # Generate Asset Database
        cursor = db.execute("""
            SELECT asset_id, name, description
            FROM assets 
            WHERE game_id = ?
            ORDER BY name
        """, (game_id,))
        assets = cursor.fetchall()
        
        # Format and save assets
        asset_lua = "return {\n    assets = {\n"
        for asset in assets:
            formatted = format_asset_as_lua(dict(asset))
            asset_lua += formatted
        asset_lua += "    },\n}"
        
        with open(db_paths['asset']['lua'], 'w', encoding='utf-8') as f:
            f.write(asset_lua)
            logger.info(f"Wrote asset database to {db_paths['asset']['lua']}")

        # Generate NPC Database - Include new coordinate columns
        cursor = db.execute("""
            SELECT 
                npc_id,
                display_name,
                asset_id,
                model,
                system_prompt,
                response_radius,
                spawn_x,
                spawn_y,
                spawn_z,
                abilities,
                enabled
            FROM npcs n
            WHERE game_id = (SELECT id FROM games WHERE slug = ?)
            AND enabled = 1
        """, (game_slug,))
        npcs = cursor.fetchall()
        
        # Format and save NPCs
        npc_lua = "return {\n    npcs = {\n"
        for npc in npcs:
            npc_lua += format_npc_as_lua(dict(npc))
        npc_lua += "\n    },\n}"
        
        with open(db_paths['npc']['lua'], 'w', encoding='utf-8') as f:
            f.write(npc_lua)
            logger.info(f"Wrote NPC database to {db_paths['npc']['lua']}")
            
    except Exception as e:
        logger.error(f"Error saving Lua databases: {str(e)}")
        raise

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
            save_lua_database(game_slug, db)
            
        elif db_type == 'npc':
            # Get NPCs from database
            cursor = db.execute("""
                SELECT npc_id, display_name, asset_id, model, system_prompt,
                       response_radius, spawn_position, abilities
                FROM npcs WHERE game_id = ?
            """, (game_id,))
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Generate Lua file - pass db connection
            save_lua_database(game_slug, db)

def sync_game_files(game_slug: str) -> None:
    """Sync both JSON and Lua files from database"""
    generate_lua_from_db(game_slug, 'asset')
    generate_lua_from_db(game_slug, 'npc')

def ensure_game_directories(game_slug: str, clone_from: Optional[str] = None) -> Dict[str, Path]:
    """Create and return game directory structure"""
    logger.info(f"Creating game directories for {game_slug}, cloning from: {clone_from}")
    
    try:
        GAMES_DIR.mkdir(parents=True, exist_ok=True)
        game_root = GAMES_DIR / game_slug
        
        # Determine source directory
        if clone_from and (GAMES_DIR / clone_from).exists():
            source_dir = GAMES_DIR / clone_from
            logger.info(f"Cloning from existing game: {source_dir}")
        else:
            source_dir = GAMES_DIR / "_template"
            logger.info(f"Using template directory: {source_dir}")
            
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found at {source_dir}")
            
        # Remove existing directory if it exists
        if game_root.exists():
            logger.info(f"Removing existing game directory: {game_root}")
            shutil.rmtree(game_root)
            
        # Copy from source
        logger.info(f"Copying from {source_dir} to {game_root}")
        shutil.copytree(source_dir, game_root, symlinks=False,
                       ignore_dangling_symlinks=True,
                       dirs_exist_ok=True)
        
        # Define and ensure all required paths exist
        paths = {
            'root': game_root,
            'src': game_root / "src",
            'data': game_root / "src" / "data",
            'assets': game_root / "src" / "assets",
            'npcs': game_root / "src" / "assets" / "npcs"
        }
        
        # Create directories if they don't exist
        for path_name, path in paths.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created {path_name} directory at: {path}")
            
        return paths
        
    except Exception as e:
        logger.error(f"Error in ensure_game_directories: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        raise

def save_databases(game_slug: str, db: sqlite3.Connection) -> None:
    """Save both Lua and JSON databases for a game"""
    try:
        cursor = db.execute("SELECT id FROM games WHERE slug = ?", (game_slug,))
        game = cursor.fetchone()
        if not game:
            raise ValueError(f"Game {game_slug} not found")
            
        game_id = game['id']
        db_paths = get_database_paths(game_slug)
        
        # Get assets with all fields
        cursor = db.execute("""
            SELECT *
            FROM assets 
            WHERE game_id = ?
            ORDER BY name
        """, (game_id,))
        assets = cursor.fetchall()
        
        # Save Lua format
        asset_lua = "return {\n    assets = {\n"
        for asset in assets:
            asset_lua += format_asset_as_lua(dict(asset))
        asset_lua += "    },\n}"
        
        with open(db_paths['asset']['lua'], 'w', encoding='utf-8') as f:
            f.write(asset_lua)
            logger.info(f"Wrote Lua asset database to {db_paths['asset']['lua']}")

        # Save JSON format
        asset_json = {"assets": [dict(asset) for asset in assets]}
        with open(db_paths['asset']['json'], 'w', encoding='utf-8') as f:
            json.dump(asset_json, f, indent=4)
            logger.info(f"Wrote JSON asset database to {db_paths['asset']['json']}")

        # Save NPCs as before...
        
    except Exception as e:
        logger.error(f"Error saving databases: {str(e)}")
        raise

def get_current_action(context: HumanContextData) -> str:
    """Determine current action from context"""
    if context.health and context.health.get('state') == 'Dead':
        return "Dead"
    elif context.health and context.health.get('current') < context.health.get('max', 100) * 0.3:
        return "Severely injured"
    elif context.health and context.health.get('current') < context.health.get('max', 100) * 0.7:
        return "Injured"
    elif context.health and context.health.get('isMoving'):
        return "Moving"
    return "Idle"  # Default action
