import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
import shutil
import os
from slugify import slugify as python_slugify
from .utils import (
    load_json_database, 
    save_json_database, 
    save_lua_database, 
    get_database_paths,
    ensure_game_directories,
    save_databases
)
from .storage import FileStorageManager
from .image_utils import get_asset_description
from .config import (
    STORAGE_DIR, 
    ASSETS_DIR, 
    THUMBNAILS_DIR, 
    AVATARS_DIR,
    get_game_paths,
    BASE_DIR
)
from .database import (
    get_db,
    fetch_all_games,
    create_game,
    fetch_game,
    update_game,
    delete_game,
    count_assets,
    count_npcs,
    fetch_assets_by_game,
    fetch_npcs_by_game
)
import uuid
from fastapi.templating import Jinja2Templates
import sqlite3
from enum import Enum
from openai import OpenAI
import numpy as np
from scipy.spatial.distance import cosine
from .security import require_admin, require_game_key

logger = logging.getLogger("roblox_app")

# dashboard_router.py

from .security import check_allowed_ips

# Comment out the security dependency
# router = APIRouter(dependencies=[Depends(check_allowed_ips)])
router = APIRouter()  # No security check

# Set up templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize OpenAI client
client = OpenAI()

def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for text"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def semantic_similarity(query_embedding: List[float], target_embedding: List[float]) -> float:
    """Calculate cosine similarity between embeddings"""
    return 1 - cosine(query_embedding, target_embedding)

def slugify(text):
    """Generate a unique slug for the game."""
    base_slug = python_slugify(text, separator='-', lowercase=True)
    slug = base_slug
    counter = 1
    
    with get_db() as db:
        while True:
            # Check if slug exists
            cursor = db.execute("SELECT 1 FROM games WHERE slug = ?", (slug,))
            if not cursor.fetchone():
                break
            # If exists, append counter and try again
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    logger.info(f"Generated unique slug: {slug} from title: {text}")
    return slug

@router.get("/api/games")
async def list_games():
    try:
        logger.info("Fetching games list")
        games = fetch_all_games()  # Using non-async version
        logger.info(f"Found {len(games)} games")
        
        formatted_games = []
        for game in games:
            game_data = {
                'id': game['id'],
                'title': game['title'],
                'slug': game['slug'],
                'description': game['description'],
                'asset_count': count_assets(game['id']),
                'npc_count': count_npcs(game['id'])
            }
            formatted_games.append(game_data)
            logger.info(f"Game: {game_data['title']} (ID: {game_data['id']}, Assets: {game_data['asset_count']}, NPCs: {game_data['npc_count']})")
        
        return JSONResponse(formatted_games)
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return JSONResponse({"error": "Failed to fetch games"}, status_code=500)

@router.get("/api/games/{slug}")
async def get_game(slug: str):
    try:
        game = fetch_game(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return JSONResponse(game)
    except Exception as e:
        logger.error(f"Error fetching game: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/games")
async def create_game_endpoint(request: Request):
    try:
        data = await request.json()
        game_slug = slugify(data['title'])
        clone_from = data.get('cloneFrom')
        
        logger.info(f"Creating game with title: {data['title']}, slug: {game_slug}, clone from: {clone_from}")
        
        try:
            # Create game directories from template
            logger.info("About to call ensure_game_directories")
            paths = ensure_game_directories(game_slug, clone_from)
            logger.info(f"Got paths back: {paths}")
            
            if not paths:
                logger.error("ensure_game_directories returned None")
                raise ValueError("Failed to create game directories - no paths returned")
                
            logger.info(f"Created game directories at: {paths['root']}")
            
            with get_db() as db:
                try:
                    # Start transaction
                    db.execute('BEGIN')
                    
                    # Create game in database
                    game_id = create_game(data['title'], game_slug, data['description'])
                    logger.info(f"Created game in database with ID: {game_id}")
                    
                    # If cloning from another game
                    if clone_from:
                        logger.info(f"Cloning data from game: {clone_from}")
                        
                        try:
                            # Get source game ID
                            cursor = db.execute("SELECT id FROM games WHERE slug = ?", (clone_from,))
                            source_game = cursor.fetchone()
                            if not source_game:
                                raise ValueError(f"Source game {clone_from} not found")
                            
                            source_game_id = source_game['id']
                            
                            # Clone assets with better error handling
                            logger.info("Cloning assets...")
                            try:
                                db.execute("""
                                    INSERT INTO assets (
                                        game_id, asset_id, name, description, image_url, type, tags,
                                        is_location, position_x, position_y, position_z,
                                        location_data, aliases
                                    )
                                    SELECT 
                                        ?, asset_id, name, description, image_url, type, tags,
                                        is_location, position_x, position_y, position_z,
                                        location_data, aliases
                                    FROM assets 
                                    WHERE game_id = ?
                                """, (game_id, source_game_id))
                                logger.info("Assets cloned successfully")
                            except Exception as e:
                                logger.error(f"Error cloning assets: {str(e)}")
                                raise
                            
                            # Clone NPCs with better error handling
                            logger.info("Cloning NPCs...")
                            try:
                                cursor = db.execute("""
                                    SELECT 
                                        display_name, asset_id, model,
                                        system_prompt, response_radius, spawn_x, spawn_y, spawn_z,
                                        abilities
                                    FROM npcs 
                                    WHERE game_id = ?
                                """, (source_game_id,))
                                
                                npcs = cursor.fetchall()
                                for npc in npcs:
                                    npc_id = str(uuid.uuid4())  # Generate new unique ID
                                    db.execute("""
                                        INSERT INTO npcs (
                                            game_id, npc_id, display_name, asset_id, model,
                                            system_prompt, response_radius, spawn_x, spawn_y, spawn_z,
                                            abilities
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        game_id,
                                        npc_id,
                                        npc['display_name'],
                                        npc['asset_id'],
                                        npc['model'],
                                        npc['system_prompt'],
                                        npc['response_radius'],
                                        npc['spawn_x'],
                                        npc['spawn_y'],
                                        npc['spawn_z'],
                                        npc['abilities']
                                    ))
                                logger.info(f"Cloned {len(npcs)} NPCs successfully")
                            except Exception as e:
                                logger.error(f"Error cloning NPCs: {str(e)}")
                                raise
                            
                            # Commit transaction
                            db.commit()
                            logger.info("Database cloning completed successfully")
                            
                        except Exception as e:
                            logger.error(f"Database error: {str(e)}")
                            db.rollback()
                            raise
                        
                    # Update project.json name
                    project_file = paths['root'] / "default.project.json"
                    if project_file.exists():
                        with open(project_file, 'r') as f:
                            project_data = json.load(f)
                        project_data['name'] = data['title']
                        with open(project_file, 'w') as f:
                            json.dump(project_data, f, indent=2)
                        logger.info("Updated project.json")
                    
                    # Initialize/update Lua databases
                    save_lua_database(game_slug, db)
                    logger.info("Generated Lua databases")
                    
                    db.commit()
                    logger.info("Database transaction committed")
                    
                    return JSONResponse({
                        "id": game_id,
                        "slug": game_slug,
                        "message": "Game created successfully"
                    })
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Database error: {str(e)}")
                    raise
                
        except Exception as e:
            logger.error(f"Failed to create game directories: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error creating game: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.put("/api/games/{slug}")
async def update_game_endpoint(slug: str, request: Request):
    try:
        data = await request.json()
        update_game(slug, data['title'], data['description'])  # Using non-async version
        return JSONResponse({"message": "Game updated successfully"})
    except Exception as e:
        logger.error(f"Error updating game: {str(e)}")
        return JSONResponse({"error": "Failed to update game"}, status_code=500)

@router.delete("/api/games/{slug}")
async def delete_game_endpoint(slug: str):
    try:
        logger.info(f"Deleting game: {slug}")
        
        with get_db() as db:
            try:
                # Start transaction
                db.execute('BEGIN')
                
                # Get game ID first
                cursor = db.execute("SELECT id FROM games WHERE slug = ?", (slug,))
                game = cursor.fetchone()
                if not game:
                    raise HTTPException(status_code=404, detail="Game not found")
                game_id = game['id']
                
                # Delete NPCs and assets first (foreign key constraints)
                db.execute("DELETE FROM npcs WHERE game_id = ?", (game_id,))
                db.execute("DELETE FROM assets WHERE game_id = ?", (game_id,))
                
                # Delete game
                db.execute("DELETE FROM games WHERE id = ?", (game_id,))
                
                # Delete game directory
                game_dir = Path(os.path.dirname(BASE_DIR)) / "games" / slug
                if game_dir.exists():
                    shutil.rmtree(game_dir)
                    logger.info(f"Deleted game directory: {game_dir}")
                
                db.commit()
                logger.info(f"Successfully deleted game {slug}")
                
                return JSONResponse({"message": "Game deleted successfully"})
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error in transaction, rolling back: {str(e)}")
                raise
            
    except Exception as e:
        logger.error(f"Error deleting game: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/assets")
async def list_assets(game_id: int = None, type: str = None):
    """Get list of assets, optionally filtered by game and type"""
    try:
        with get_db() as db:
            # Update SELECT to include location fields
            query = """
                SELECT id, asset_id, name, description, image_url, type, tags, 
                       game_id, created_at, location_data, is_location,
                       position_x, position_y, position_z, aliases
                FROM assets
                WHERE 1=1
            """
            params = []
            
            if game_id:
                query += " AND game_id = ?"
                params.append(game_id)
                
            if type:
                query += " AND type = ?"
                params.append(type)
                
            logger.info(f"Fetching assets for game_id: {game_id}, type: {type}")
            cursor = db.execute(query, params)
            assets = cursor.fetchall()
            
            # Convert to list of dicts and parse JSON fields
            asset_list = []
            for asset in assets:
                asset_dict = dict(asset)
                # Parse JSON fields
                if asset_dict.get('location_data'):
                    asset_dict['location_data'] = json.loads(asset_dict['location_data'])
                if asset_dict.get('aliases'):
                    asset_dict['aliases'] = json.loads(asset_dict['aliases'])
                asset_list.append(asset_dict)
            
            logger.info(f"Found {len(assets)} assets")
            return {"assets": asset_list}
            
    except Exception as e:
        logger.error(f"Error fetching assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_valid_npcs(db, game_id):
    """Get only valid NPCs (with required fields and valid assets)"""
    cursor = db.execute("""
        SELECT n.*, a.name as asset_name, a.image_url
        FROM npcs n
        JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
        WHERE n.game_id = ?
            AND n.display_name IS NOT NULL 
            AND n.display_name != ''
            AND n.asset_id IS NOT NULL 
            AND n.asset_id != ''
        ORDER BY n.display_name
    """, (game_id,))
    return cursor.fetchall()

@router.get("/api/npcs")
async def list_npcs(game_id: Optional[int] = None):
    try:
        with get_db() as db:
            if game_id:
                cursor = db.execute("""
                    SELECT DISTINCT
                        n.id,
                        n.npc_id,
                        n.display_name,
                        n.asset_id,
                        n.model,
                        n.system_prompt,
                        n.response_radius,
                        n.spawn_x,
                        n.spawn_y,
                        n.spawn_z,
                        n.abilities,
                        n.enabled,
                        a.name as asset_name,
                        a.image_url
                    FROM npcs n
                    JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                    WHERE n.game_id = ?
                    ORDER BY n.display_name
                """, (game_id,))
            
            npcs = [dict(row) for row in cursor.fetchall()]
            
            # Format the response with new coordinate structure
            formatted_npcs = []
            for npc in npcs:
                npc_data = {
                    "id": npc["id"],
                    "npcId": npc["npc_id"],
                    "displayName": npc["display_name"],
                    "assetId": npc["asset_id"],
                    "assetName": npc["asset_name"],
                    "model": npc["model"],
                    "systemPrompt": npc["system_prompt"],
                    "responseRadius": npc["response_radius"],
                    "spawnPosition": {
                        "x": npc["spawn_x"],
                        "y": npc["spawn_y"],
                        "z": npc["spawn_z"]
                    },
                    "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                    "imageUrl": npc["image_url"],
                    "enabled": bool(npc["enabled"])  # Convert to boolean
                }
                formatted_npcs.append(npc_data)
            
            return JSONResponse({"npcs": formatted_npcs})
            
    except Exception as e:
        logger.error(f"Error fetching NPCs: {str(e)}")
        return JSONResponse({"error": "Failed to fetch NPCs"}, status_code=500)

@router.put("/api/games/{game_id}/assets/{asset_id}")
async def update_asset(game_id: int, asset_id: str, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating asset {asset_id} with data: {json.dumps(data, indent=2)}")
        
        with get_db() as db:
            try:
                # Update asset with new location fields
                update_sql = """
                    UPDATE assets 
                    SET name = ?,
                        description = ?,
                        type = ?,
                        is_location = ?,
                        position_x = ?,
                        position_y = ?,
                        position_z = ?,
                        aliases = ?,
                        location_data = ?
                    WHERE game_id = ? AND asset_id = ?
                    RETURNING *
                """
                
                params = (
                    data['name'],
                    data['description'],
                    data['type'],
                    data.get('is_location', False),
                    data.get('position_x'),
                    data.get('position_y'),
                    data.get('position_z'),
                    json.dumps(data.get('aliases', [])),
                    json.dumps(data.get('location_data', {})),
                    game_id,
                    asset_id
                )
                
                logger.info(f"Executing SQL with params: {params}")
                cursor = db.execute(update_sql, params)
                
                updated = cursor.fetchone()
                if not updated:
                    logger.error(f"Asset not found: game_id={game_id}, asset_id={asset_id}")
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                logger.info(f"Successfully updated asset: {dict(updated)}")
                db.commit()
                
                # Get game slug for file updates
                cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
                game = cursor.fetchone()
                if game:
                    # Update Lua and JSON files
                    save_databases(game['slug'], db)
                
                return JSONResponse(dict(updated))
                
            except sqlite3.Error as e:
                logger.error(f"Database error: {str(e)}")
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error updating asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str, game_id: int):
    """Get a single NPC by ID"""
    try:
        logger.info(f"Fetching NPC {npc_id} for game {game_id}")
        
        with get_db() as db:
            # Get NPC with asset info
            cursor = db.execute("""
                SELECT n.*, a.name as asset_name, a.image_url
                FROM npcs n
                LEFT JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            
            npc = cursor.fetchone()
            if not npc:
                logger.error(f"NPC not found: {npc_id}")
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Convert sqlite3.Row to dict
            npc = dict(npc)
            
            # Format response
            npc_data = {
                "id": npc["id"],
                "npcId": npc["npc_id"],
                "displayName": npc["display_name"],
                "assetId": npc["asset_id"],
                "assetName": npc["asset_name"],
                "systemPrompt": npc["system_prompt"],
                "responseRadius": npc["response_radius"],
                "spawnPosition": {
                    "x": npc["spawn_x"],
                    "y": npc["spawn_y"],
                    "z": npc["spawn_z"]
                },
                "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                "imageUrl": npc["image_url"]
            }
            
            logger.info(f"Found NPC: {npc_data}")
            return JSONResponse(npc_data)
            
    except Exception as e:
        logger.error(f"Error fetching NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/npcs/{npc_id}")
async def update_npc(npc_id: str, game_id: int, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating NPC {npc_id} with data: {data}")
        
        with get_db() as db:
            # First get game info for Lua update
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            
            game_slug = game['slug']
            
            # Extract and validate spawn coordinates
            spawn_pos = data.get('spawnPosition', {})
            try:
                spawn_x = float(spawn_pos.get('x', 0))
                spawn_y = float(spawn_pos.get('y', 5))
                spawn_z = float(spawn_pos.get('z', 0))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid spawn coordinates"
                )
            
            # Get cursor from db connection
            cursor = db.cursor()
            
            # Update NPC with new coordinate columns
            cursor.execute("""
                UPDATE npcs 
                SET display_name = ?,
                    asset_id = ?,
                    system_prompt = ?,
                    response_radius = ?,
                    spawn_x = ?,
                    spawn_y = ?,
                    spawn_z = ?,
                    abilities = ?
                WHERE npc_id = ? AND game_id = ?
            """, (
                data['displayName'],
                data['assetId'],
                data['systemPrompt'],
                data['responseRadius'],
                spawn_x,
                spawn_y,
                spawn_z,
                json.dumps(data['abilities']),
                npc_id,
                game_id
            ))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Fetch updated NPC data
            cursor.execute("""
                SELECT n.*, a.name as asset_name, a.image_url
                FROM npcs n
                LEFT JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            
            updated = cursor.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Updated NPC not found")
            
            # Convert sqlite3.Row to dict before accessing with get()
            updated_dict = dict(updated)
            
            # Format response with new coordinate structure
            npc_data = {
                "id": updated_dict["id"],
                "npcId": updated_dict["npc_id"],
                "displayName": updated_dict["display_name"],
                "assetId": updated_dict["asset_id"],
                "assetName": updated_dict.get("asset_name"),  # Now we can use .get()
                "systemPrompt": updated_dict["system_prompt"],
                "responseRadius": updated_dict["response_radius"],
                "spawnPosition": {  # Format coordinates for frontend
                    "x": updated_dict["spawn_x"],
                    "y": updated_dict["spawn_y"],
                    "z": updated_dict["spawn_z"]
                },
                "abilities": json.loads(updated_dict["abilities"]) if updated_dict["abilities"] else [],
                "imageUrl": updated_dict.get("image_url")  # Now we can use .get()
            }
            
            # Update Lua files
            save_lua_database(game_slug, db)
            
            db.commit()
            return JSONResponse(npc_data)
            
    except Exception as e:
        logger.error(f"Error updating NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/games/current")
async def get_current_game():
    """Get the current active game"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT id, title, slug, description
                FROM games
                WHERE slug = 'game1'  # Default to game1 for now
            """)
            game = cursor.fetchone()
            if game:
                return JSONResponse({
                    "id": game["id"],
                    "title": game["title"],
                    "slug": game["slug"],
                    "description": game["description"]
                })
            return JSONResponse({"error": "No active game found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error getting current game: {str(e)}")
        return JSONResponse({"error": "Failed to get current game"}, status_code=500)

class AssetType(str, Enum):
    MODEL = "Model"
    MESH = "Mesh"
    DECAL = "Decal"
    ANIMATION = "Animation"
    PLUGIN = "Plugin"
    SOUND = "Sound"
    TEXTURE = "Texture"
    CLOTHING = "Clothing"
    PACKAGE = "Package"
    BADGE = "Badge"
    GAMEPASS = "GamePass"
    FONT = "Font"
    SCRIPT = "Script"
    MATERIAL_VARIANT = "MaterialVariant"
    MESH_PART = "MeshPart"
    SURFACE_APPEARANCE = "SurfaceAppearance"
    # Keep existing types
    NPC = "NPC"
    VEHICLE = "Vehicle"
    BUILDING = "Building"
    PROP = "Prop"

@router.post("/api/assets/create")
async def create_asset(
    request: Request,
    game_id: int = Form(...),
    asset_id: str = Form(...),
    name: str = Form(...),
    type: AssetType = Form(...),
    file: Optional[UploadFile] = File(None)
):
    try:
        logger.info(f"Received asset creation request:")
        logger.info(f"game_id: {game_id}")
        logger.info(f"asset_id: {asset_id}")
        logger.info(f"name: {name}")
        logger.info(f"type: {type}")
        logger.info(f"file: {file.filename if file else 'No file'}")
        
        # Get game info
        with get_db() as db:
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            game_slug = game['slug']

            # Delete existing asset if any
            cursor.execute("""
                DELETE FROM assets 
                WHERE asset_id = ? AND game_id = ?
            """, (asset_id, game_id))
            
            # Get and validate game paths
            game_paths = get_game_paths(game_slug)
            logger.info(f"Game paths received: {game_paths}")
            
            if game_slug not in game_paths:
                logger.error(f"Game slug {game_slug} not found in paths: {game_paths}")
                raise HTTPException(status_code=500, detail="Game path not found")
                
            game_path_data = game_paths[game_slug]
            root_path = game_path_data['root']
            
            # Construct the correct assets path
            assets_path = root_path / 'src' / 'assets'
            logger.info(f"Using assets path: {assets_path}")
            
            # Only save file if one was provided
            if file:
                asset_type_dir = type.lower() + 's'
                asset_dir = assets_path / asset_type_dir
                logger.info(f"Creating asset directory: {asset_dir}")
                asset_dir.mkdir(parents=True, exist_ok=True)
                file_path = asset_dir / f"{asset_id}.rbxm"
                logger.info(f"Saving file to: {file_path}")

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

            # Get description using utility
            description_data = await get_asset_description(
                asset_id=asset_id, 
                name=name
            )
            
            logger.info(f"Description data received: {description_data}")
            
            if description_data:
                description = description_data.get('description')
                image_url = description_data.get('imageUrl')
                logger.info(f"Got image URL from description: {image_url}")
            else:
                description = None
                image_url = None
            
            cursor.execute("""
                INSERT INTO assets (
                    game_id, 
                    asset_id, 
                    name, 
                    description, 
                    type,
                    image_url
                ) VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (
                game_id,
                asset_id,
                name,
                description,
                type,
                image_url
            ))
            db_id = cursor.fetchone()['id']
            db.commit()
            
            save_lua_database(game_slug, db)
            
            return JSONResponse({
                "id": db_id,
                "asset_id": asset_id,
                "name": name,
                "description": description,
                "type": type,
                "image_url": image_url,
                "message": "Asset created successfully"
            })
                
    except Exception as e:
        logger.error(f"Error creating asset: {str(e)}")
        logger.error(f"Error class: {e.__class__.__name__}")
        logger.error(f"Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/npcs")
async def create_npc(
    request: Request,
    game_id: int = Form(...),
    displayName: str = Form(...),
    assetID: str = Form(...),
    system_prompt: str = Form(None),
    responseRadius: int = Form(20),
    spawnX: float = Form(0),
    spawnY: float = Form(5),
    spawnZ: float = Form(0),
    abilities: str = Form("[]")
):
    try:
        logger.info(f"Creating NPC with asset_id: {assetID}")
        
        with get_db() as db:
            # First get game info for Lua update
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            
            game_slug = game['slug']  # Get slug before creating NPC
            
            # Verify asset exists
            cursor = db.execute(
                "SELECT asset_id FROM assets WHERE asset_id = ? AND game_id = ?",
                (assetID, game_id)
            )
            asset = cursor.fetchone()
            if not asset:
                raise HTTPException(
                    status_code=400,
                    detail=f"Asset {assetID} not found"
                )
            
            # Create NPC with verified asset_id
            npc_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO npcs (
                    game_id, npc_id, display_name, asset_id,
                    system_prompt, response_radius,
                    spawn_x, spawn_y, spawn_z, abilities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id, npc_id, displayName, assetID,
                system_prompt, responseRadius,
                spawnX, spawnY, spawnZ, abilities
            ))
            db.commit()
            
            # Now we have game_slug defined
            save_lua_database(game_slug, db)
            
            logger.info(f"Created NPC {displayName} with asset_id {assetID}")
            
            return {
                "success": True,
                "npc_id": npc_id,
                "message": "NPC created successfully"
            }
            
    except Exception as e:
        logger.error(f"Error creating NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/npcs/{npc_id}")
async def delete_npc(npc_id: str, game_id: int):
    try:
        logger.info(f"Deleting NPC {npc_id} from game {game_id}")
        
        with get_db() as db:
            # Get NPC and game info first
            cursor = db.execute("""
                SELECT n.*, g.slug 
                FROM npcs n
                JOIN games g ON n.game_id = g.id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            npc = cursor.fetchone()
            
            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            game_slug = npc['slug']  # Get slug from joined query
            
            # Delete the database entry
            cursor.execute("""
                DELETE FROM npcs 
                WHERE npc_id = ? AND game_id = ?
            """, (npc_id, game_id))
            
            db.commit()
            
            # Update Lua files with game_slug
            save_lua_database(game_slug, db)
            
            return JSONResponse({"message": "NPC deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/games/{game_id}/assets/{asset_id}")
async def delete_asset(game_id: int, asset_id: str):
    try:
        logger.info(f"Deleting asset {asset_id} from game {game_id}")
        
        with get_db() as db:
            try:
                # First get game info
                cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
                game = cursor.fetchone()
                if not game:
                    raise HTTPException(status_code=404, detail="Game not found")
                
                game_slug = game['slug']
                
                # Delete any NPCs using this asset
                cursor.execute("""
                    DELETE FROM npcs 
                    WHERE game_id = ? AND asset_id = ?
                """, (game_id, asset_id))
                
                # Delete the asset
                cursor.execute("""
                    DELETE FROM assets 
                    WHERE game_id = ? AND asset_id = ?
                """, (game_id, asset_id))
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                # Update Lua files
                save_lua_database(game_slug, db)
                
                db.commit()
                return JSONResponse({"message": "Asset deleted successfully"})
                
            except Exception as e:
                db.rollback()
                logger.error(f"Database error deleting asset: {str(e)}")
                raise
            
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update the dashboard_new route
@router.get("/dashboard/new")
async def dashboard_new(request: Request):
    """Render the new version of the dashboard"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id, title, slug, description 
            FROM games 
            ORDER BY created_at DESC
        """)
        games = cursor.fetchall()
        
    return templates.TemplateResponse(
        "dashboard_new.html", 
        {
            "request": request,
            "games": games
        }
    )

@router.get("/api/games/templates")
async def get_game_templates():
    """Get list of games available for cloning"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT id, title, slug, description 
                FROM games 
                ORDER BY created_at DESC
            """)
            templates = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Found {len(templates)} available templates")
            return JSONResponse({"templates": templates})
            
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/assets/add")
async def add_asset(
    name: str,
    description: str,
    is_location: bool = False,
    position_x: Optional[float] = None,
    position_y: Optional[float] = None,
    position_z: Optional[float] = None,
    aliases: str = "[]"  # Comma-separated list in form, stored as JSON
):
    """Add new asset with location support"""
    try:
        # Parse aliases from comma-separated string
        alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
        
        db.execute("""
            INSERT INTO assets (
                name, description, is_location, 
                position_x, position_y, position_z,
                aliases
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, description, is_location,
            position_x, position_y, position_z,
            json.dumps(alias_list)
        ))
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Define response models
class LocationData(BaseModel):
    area: str = Field(..., description="The zone this location belongs to")
    type: str = Field(..., description="Type of location (shop, landmark, etc)")
    owner: Optional[str] = Field(None, description="Who owns/manages this location")
    interactable: bool = Field(False, description="Whether players can interact with this")
    tags: List[str] = Field(default_factory=list, description="Categories/tags for this location")

class Asset(BaseModel):
    id: int
    asset_id: str
    name: str
    description: Optional[str]
    type: str
    is_location: bool = False
    position_x: Optional[float]
    position_y: Optional[float]
    position_z: Optional[float]
    location_data: Optional[LocationData]
    aliases: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "asset_id": "96144138651755",
                "name": "Pete's Merch Stand",
                "type": "Prop",
                "is_location": True,
                "position_x": -10.289,
                "position_y": 21.512,
                "position_z": -127.797,
                "location_data": {
                    "area": "spawn_area",
                    "type": "shop",
                    "owner": "Pete",
                    "interactable": True,
                    "tags": ["shop", "retail"]
                },
                "aliases": ["stand", "merchant stand"]
            }
        }

@router.get("/api/locations")
async def get_locations(
    game_id: Optional[int] = Query(None, description="Filter by game ID"),
    area: Optional[str] = Query(None, description="Filter by area name")
):
    """Get all location data from SQLite"""
    try:
        with get_db() as db:
            query = """
                SELECT 
                    name,
                    description,
                    slug,
                    position_x,
                    position_y,
                    position_z,
                    location_data,
                    aliases
                FROM assets
                WHERE is_location = TRUE
            """
            params = []
            
            if game_id:
                query += " AND game_id = ?"
                params.append(game_id)
                
            if area:
                query += " AND json_extract(location_data, '$.area') = ?"
                params.append(area)
                
            cursor = db.execute(query, params)
            locations = cursor.fetchall()
            
            # Format locations as proposed
            formatted_locations = {
                "locations": [
                    {
                        "name": loc["name"],
                        "description": loc["description"],
                        "coordinates": [
                            loc["position_x"],
                            loc["position_y"],
                            loc["position_z"]
                        ],
                        "slug": loc["slug"],
                        **json.loads(loc["location_data"] or "{}"),
                        "aliases": json.loads(loc["aliases"] or "[]")
                    } for loc in locations
                ]
            }
            
            return formatted_locations
            
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/assets/{asset_id}")
async def get_asset(asset_id: str, game_id: int = None):
    """Get single asset by ID"""
    try:
        with get_db() as db:
            query = """
                SELECT *
                FROM assets
                WHERE asset_id = ?
            """
            params = [asset_id]
            
            if game_id:
                query += " AND game_id = ?"
                params.append(game_id)
                
            cursor = db.execute(query, params)
            asset = cursor.fetchone()
            
            if not asset:
                raise HTTPException(status_code=404, detail="Asset not found")
                
            # Parse JSON fields
            asset_dict = dict(asset)
            if asset_dict.get('location_data'):
                asset_dict['location_data'] = json.loads(asset_dict['location_data'])
            if asset_dict.get('aliases'):
                asset_dict['aliases'] = json.loads(asset_dict['aliases'])
                
            return asset_dict
            
    except Exception as e:
        logger.error(f"Error fetching asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/locations/search")
async def search_locations(
    game_id: int,
    x: float = None,
    y: float = None,
    z: float = None,
    radius: float = 10.0,
    area: str = None
):
    """Search for locations near a point"""
    try:
        with get_db() as db:
            # Base query with distance calculation
            query = """
                SELECT *, 
                    ((position_x - ?) * (position_x - ?) + 
                     (position_y - ?) * (position_y - ?) + 
                     (position_z - ?) * (position_z - ?)) as distance
                FROM assets
                WHERE is_location = TRUE
                AND game_id = ?
            """
            params = [x or 0, x or 0, y or 0, y or 0, z or 0, z or 0, game_id]
            
            if area:
                query += " AND json_extract(location_data, '$.area') = ?"
                params.append(area)
            
            # Add distance filter to WHERE clause instead of HAVING
            if all([x, y, z]):
                query += f" AND ((position_x - ?) * (position_x - ?) + \
                               (position_y - ?) * (position_y - ?) + \
                               (position_z - ?) * (position_z - ?)) <= ?"
                params.extend([x, x, y, y, z, z, radius * radius])
                
            query += " ORDER BY distance"
            
            cursor = db.execute(query, params)
            locations = cursor.fetchall()
            
            # Parse JSON fields
            location_list = []
            for loc in locations:
                loc_dict = dict(loc)
                if loc_dict.get('location_data'):
                    loc_dict['location_data'] = json.loads(loc_dict['location_data'])
                if loc_dict.get('aliases'):
                    loc_dict['aliases'] = json.loads(loc_dict['aliases'])
                location_list.append(loc_dict)
            
            return {"locations": location_list}
            
    except Exception as e:
        logger.error(f"Error searching locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/locations/semantic-search")
async def semantic_location_search(
    game_id: int,
    query: str,
    threshold: float = Query(0.8, description="Minimum similarity threshold (0-1)"),
    limit: int = Query(3, description="Maximum number of results to return")
):
    """Search locations using semantic similarity"""
    try:
        # Add context to query
        contextualized_query = f"Find a location in the game: {query}"
        query_embedding = get_embedding(contextualized_query)
        
        with get_db() as db:
            cursor = db.execute("""
                SELECT id, asset_id, name, description, 
                       position_x, position_y, position_z,
                       location_data, aliases
                FROM assets
                WHERE is_location = TRUE
                AND game_id = ?
            """, (game_id,))
            
            locations = []
            for loc in cursor.fetchall():
                loc_dict = dict(loc)
                
                # Parse JSON fields
                if loc_dict.get('location_data'):
                    loc_dict['location_data'] = json.loads(loc_dict['location_data'])
                if loc_dict.get('aliases'):
                    loc_dict['aliases'] = json.loads(loc_dict['aliases'])
                
                # Create more structured searchable text
                location_data = loc_dict.get('location_data', {})
                search_text = f"""
                This is a location in the game:
                Name: {loc_dict['name']}
                Description: {loc_dict['description']}
                Type: {location_data.get('type', '')}
                Area: {location_data.get('area', '')}
                Owner: {location_data.get('owner', '')}
                Also known as: {' '.join(loc_dict.get('aliases', []))}
                """
                
                # Get embedding for location
                loc_embedding = get_embedding(search_text)
                
                # Calculate similarity
                similarity = semantic_similarity(query_embedding, loc_embedding)
                
                if similarity >= threshold:
                    locations.append({
                        **loc_dict,
                        "similarity": similarity
                    })
            
            # Sort by similarity and limit results
            locations.sort(key=lambda x: x["similarity"], reverse=True)
            locations = locations[:limit]
            
            if not locations:
                return {
                    "message": "No matching locations found",
                    "locations": []
                }
            
            return {
                "message": f"Found {len(locations)} matching locations",
                "locations": locations
            }
            
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Public chat endpoint
@router.post("/api/chat/v2")
async def chat_with_npc_v2(
    request: Request,
    npc_id: str,
    message: str,
    conversation_id: Optional[str] = None
):
    """Public chat endpoint"""
    try:
        # Process chat request
        response = await process_chat(npc_id, message, conversation_id)
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/npcs/{npc_id}/toggle")
async def toggle_npc(npc_id: str, request: Request):
    try:
        body = await request.json()
        enabled = bool(body.get('enabled'))
        logger.debug(f"Toggling NPC {npc_id} to {enabled}")
        
        with get_db() as db:
            # First get game info for Lua update
            cursor = db.execute("""
                SELECT g.slug 
                FROM games g 
                JOIN npcs n ON n.game_id = g.id 
                WHERE n.npc_id = ?
            """, (npc_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            game_slug = game['slug']
            
            db.execute(
                "UPDATE npcs SET enabled = ? WHERE npc_id = ?",
                (enabled, npc_id)
            )
            db.commit()
            
            # Verify the update
            cursor = db.execute(
                "SELECT enabled FROM npcs WHERE npc_id = ?",
                (npc_id,)
            )
            result = cursor.fetchone()
            logger.debug(f"Updated NPC {npc_id}, new enabled state: {result['enabled']}")
            
            # Update Lua files
            save_lua_database(game_slug, db)
            logger.info(f"Updated Lua database for game {game_slug}")
            
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to toggle NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ... rest of your existing routes ...



