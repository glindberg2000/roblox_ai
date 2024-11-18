import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
import shutil
import os
from slugify import slugify as python_slugify
from .utils import load_json_database, save_json_database, save_lua_database, get_database_paths
from .storage import FileStorageManager
from .image_utils import get_asset_description
from .config import (
    STORAGE_DIR, 
    ASSETS_DIR, 
    THUMBNAILS_DIR, 
    AVATARS_DIR,
    ensure_game_directories,
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

logger = logging.getLogger("roblox_app")
router = APIRouter()

# Set up templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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
        
        logger.info(f"Creating game with title: {data['title']}, slug: {game_slug}, clone_from: {clone_from}")
        
        # Create game directories
        ensure_game_directories(game_slug)
        
        with get_db() as db:
            try:
                # Start transaction
                db.execute('BEGIN')
                
                # Create game in database first
                game_id = create_game(data['title'], game_slug, data['description'])
                
                if clone_from:
                    # Get source game ID
                    cursor = db.execute("SELECT id FROM games WHERE slug = ?", (clone_from,))
                    source_game = cursor.fetchone()
                    if not source_game:
                        raise HTTPException(status_code=404, detail="Source game not found")
                    source_game_id = source_game['id']
                    
                    # Copy assets
                    cursor.execute("""
                        INSERT INTO assets (game_id, asset_id, name, description, type, image_url, tags)
                        SELECT ?, asset_id, name, description, type, image_url, tags
                        FROM assets WHERE game_id = ?
                    """, (game_id, source_game_id))
                    
                    # Copy NPCs
                    cursor.execute("""
                        SELECT * FROM npcs WHERE game_id = ?
                    """, (source_game_id,))
                    source_npcs = cursor.fetchall()
                    
                    # Copy NPCs with new IDs
                    for npc in source_npcs:
                        new_npc_id = f"npc_{game_id}_{npc['npc_id']}"
                        cursor.execute("""
                            INSERT INTO npcs (
                                game_id, npc_id, asset_id, display_name, model,
                                system_prompt, response_radius, spawn_position, abilities
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            game_id,
                            new_npc_id,
                            npc['asset_id'],
                            npc['display_name'],
                            npc['model'],
                            npc['system_prompt'],
                            npc['response_radius'],
                            npc['spawn_position'],
                            npc['abilities']
                        ))
                    
                    # Copy files
                    source_game_dir = Path(os.path.dirname(BASE_DIR)) / "games" / clone_from
                    target_game_dir = Path(os.path.dirname(BASE_DIR)) / "games" / game_slug
                    
                    # Copy directory structure
                    dirs_to_copy = [
                        "src/assets/npcs",
                        "src/assets/unknown",
                        "src/client",
                        "src/data",
                        "src/server",
                        "src/shared/modules"
                    ]
                    
                    for dir_path in dirs_to_copy:
                        source_dir = source_game_dir / dir_path
                        target_dir = target_game_dir / dir_path
                        
                        if source_dir.exists():
                            target_dir.parent.mkdir(parents=True, exist_ok=True)
                            if target_dir.exists():
                                shutil.rmtree(target_dir)
                            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
                    
                    # Copy specific files
                    files_to_copy = [
                        "default.project.json",
                        "src/client/NPCClientHandler.client.lua",
                        "src/server/AssetInitializer.server.lua",
                        "src/server/InteractionController.lua",
                        "src/server/Logger.lua",
                        "src/server/MainNPCScript.server.lua",
                        "src/server/NPCConfigurations.lua",
                        "src/server/NPCSystemInitializer.server.lua",
                        "src/server/PlayerJoinHandler.server.lua",
                        "src/shared/modules/AssetModule.lua",
                        "src/shared/modules/NPCManagerV3.lua"
                    ]
                    
                    for file_path in files_to_copy:
                        source_file = source_game_dir / file_path
                        target_file = target_game_dir / file_path
                        
                        if source_file.exists():
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_file, target_file)
                    
                    # Update project.json name
                    project_file = target_game_dir / "default.project.json"
                    if project_file.exists():
                        with open(project_file, 'r') as f:
                            project_data = json.load(f)
                        project_data['name'] = data['title']
                        with open(project_file, 'w') as f:
                            json.dump(project_data, f, indent=2)
                
                # Commit transaction
                db.commit()
                
                return JSONResponse({
                    "id": game_id,
                    "slug": game_slug,
                    "message": "Game created successfully"
                })
                
            except Exception as e:
                # Rollback transaction on error
                db.rollback()
                if "UNIQUE constraint failed" in str(e):
                    return JSONResponse({
                        "error": "A game with this name already exists"
                    }, status_code=400)
                raise e
            
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
async def list_assets(game_id: Optional[int] = None):
    try:
        with get_db() as db:
            logger.info(f"Fetching assets for game_id: {game_id}")
            
            # Build query based on game_id
            if game_id:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id AND n.game_id = a.game_id
                    WHERE a.game_id = ?
                    GROUP BY a.id, a.asset_id
                    ORDER BY a.name
                """, (game_id,))
            else:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count, g.title as game_title
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id AND n.game_id = a.game_id
                    LEFT JOIN games g ON a.game_id = g.id
                    GROUP BY a.id, a.asset_id
                    ORDER BY a.name
                """)
            
            assets = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Found {len(assets)} assets")
            
            # Format the response
            formatted_assets = []
            for asset in assets:
                formatted_assets.append({
                    "id": asset["id"],
                    "assetId": asset["asset_id"],
                    "name": asset["name"],
                    "description": asset["description"],
                    "imageUrl": asset["image_url"],
                    "type": asset["type"],
                    "tags": json.loads(asset["tags"]) if asset["tags"] else [],
                    "npcCount": asset["npc_count"],
                    "gameTitle": asset.get("game_title")
                })
            
            return JSONResponse({"assets": formatted_assets})
    except Exception as e:
        logger.error(f"Error fetching assets: {str(e)}")
        return JSONResponse({"error": f"Failed to fetch assets: {str(e)}"}, status_code=500)

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
                        n.spawn_position,
                        n.abilities,
                        a.name as asset_name,
                        a.image_url
                    FROM npcs n
                    JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                    WHERE n.game_id = ?
                    ORDER BY n.display_name
                """, (game_id,))
            else:
                cursor = db.execute("""
                    SELECT DISTINCT
                        n.id,
                        n.npc_id,
                        n.display_name,
                        n.asset_id,
                        n.model,
                        n.system_prompt,
                        n.response_radius,
                        n.spawn_position,
                        n.abilities,
                        a.name as asset_name,
                        a.image_url,
                        g.title as game_title
                    FROM npcs n
                    JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
                    JOIN games g ON n.game_id = g.id
                    ORDER BY n.display_name
                """)
            
            npcs = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Found {len(npcs)} unique NPCs")
            
            # Format the response
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
                    "spawnPosition": json.loads(npc["spawn_position"]) if npc["spawn_position"] else {},
                    "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                    "imageUrl": npc["image_url"],
                    "gameTitle": npc.get("game_title")
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
        logger.info(f"=== Updating asset {asset_id} for game {game_id} ===")
        
        with get_db() as db:
            # First get game info
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                logger.error(f"Game not found: {game_id}")
                return JSONResponse({"error": "Game not found"}, status_code=404)
                
            game_slug = game['slug']
            logger.info(f"Found game: {game_slug}")
            
            # Update asset in database
            cursor.execute("""
                UPDATE assets 
                SET name = ?, description = ?
                WHERE asset_id = ? AND game_id = ?
            """, (data['name'], data['description'], asset_id, game_id))
            
            if cursor.rowcount == 0:
                logger.error(f"Asset not found: {asset_id} in game {game_id}")
                return JSONResponse({"error": "Asset not found"}, status_code=404)
            
            # Get all assets for this game to update files
            cursor.execute("""
                SELECT asset_id, name, description, type, image_url, tags
                FROM assets WHERE game_id = ?
            """, (game_id,))
            all_assets = cursor.fetchall()
            
            # Format assets for Lua
            formatted_assets = [{
                "assetId": asset["asset_id"],
                "name": asset["name"],
                "description": asset["description"],
                "type": asset["type"],
                "imageUrl": asset["image_url"],
                "tags": json.loads(asset["tags"]) if asset["tags"] else []
            } for asset in all_assets]
            
            # Update JSON and Lua files
            db_paths = get_database_paths(game_slug)
            
            # Save JSON
            save_json_database(db_paths['asset']['json'], {
                "assets": formatted_assets
            })
            
            # Save Lua
            save_lua_database(db_paths['asset']['lua'], {
                "assets": formatted_assets
            })
            
            logger.info(f"Updated files for game {game_slug}")
            logger.info(f"JSON: {db_paths['asset']['json']}")
            logger.info(f"Lua: {db_paths['asset']['lua']}")
            
            db.commit()
            
            return JSONResponse({"message": "Asset updated successfully"})
            
    except Exception as e:
        logger.error(f"Error updating asset: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str):
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT n.*, a.name as asset_name, a.image_url,
                       n.system_prompt as personality
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.id = ?
            """, (npc_id,))
            npc = cursor.fetchone()
            
            if not npc:
                return JSONResponse({"error": "NPC not found"}, status_code=404)
            
            # Format NPC data
            npc_data = {
                "id": npc["id"],
                "npcId": npc["npc_id"],
                "displayName": npc["display_name"],
                "assetId": npc["asset_id"],
                "assetName": npc["asset_name"],
                "model": npc["model"],
                "personality": npc["system_prompt"],
                "systemPrompt": npc["system_prompt"],
                "responseRadius": npc["response_radius"],
                "spawnPosition": json.loads(npc["spawn_position"]) if npc["spawn_position"] else {},
                "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                "imageUrl": npc["image_url"]
            }
            return JSONResponse(npc_data)
    except Exception as e:
        logger.error(f"Error fetching NPC: {str(e)}")
        return JSONResponse({"error": "Failed to fetch NPC"}, status_code=500)

@router.put("/api/npcs/{npc_id}")
async def update_npc(npc_id: str, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating NPC {npc_id} with data: {data}")
        
        with get_db() as db:
            # First get the game_id for this NPC
            cursor = db.execute("""
                SELECT n.*, g.slug 
                FROM npcs n
                JOIN games g ON n.game_id = g.id
                WHERE n.id = ?
            """, (npc_id,))
            current_npc = cursor.fetchone()
            
            if not current_npc:
                logger.error(f"NPC not found: {npc_id}")
                return JSONResponse({"error": "NPC not found"}, status_code=404)
            
            game_slug = current_npc['slug']
            logger.info(f"Found NPC in game: {game_slug}")
            
            # Get database paths for this specific game
            db_paths = get_database_paths(game_slug)
            logger.info(f"Using paths: {db_paths}")
            
            # Update NPC in database
            db.execute("""
                UPDATE npcs 
                SET display_name = ?,
                    asset_id = ?,
                    model = ?,
                    system_prompt = ?,
                    response_radius = ?,
                    spawn_position = ?,
                    abilities = ?
                WHERE id = ?
            """, (
                data['displayName'],
                data['assetId'],
                data.get('model', ''),
                data.get('systemPrompt', ''),
                data.get('responseRadius', 20),
                json.dumps(data.get('spawnPosition', {})),
                json.dumps(data.get('abilities', [])),
                npc_id
            ))
            
            db.commit()
            logger.info("Database updated successfully")
            
            # Update JSON file
            try:
                npc_database = load_json_database(db_paths['npc']['json'])
                logger.info(f"Loaded JSON from {db_paths['npc']['json']}")
                
                for npc in npc_database.get("npcs", []):
                    if str(npc.get("id")) == str(current_npc["npc_id"]):
                        npc.update({
                            "displayName": data['displayName'],
                            "assetId": data['assetId'],
                            "model": data.get('model', ''),
                            "system_prompt": data.get('systemPrompt', ''),
                            "responseRadius": data.get('responseRadius', 20),
                            "spawnPosition": data.get('spawnPosition', {}),
                            "abilities": data.get('abilities', [])
                        })
                        logger.info("Updated NPC in JSON data")
                        break
                
                # Save both JSON and Lua files
                save_json_database(db_paths['npc']['json'], npc_database)
                logger.info(f"Saved JSON to {db_paths['npc']['json']}")
                
                save_lua_database(db_paths['npc']['lua'], {"npcs": npc_database.get("npcs", [])})
                logger.info(f"Saved Lua to {db_paths['npc']['lua']}")
            except Exception as e:
                logger.error(f"Error updating files: {e}")
                raise
            
            # Get updated NPC with asset info
            cursor = db.execute("""
                SELECT n.*, a.name as asset_name, a.image_url,
                       n.system_prompt as personality
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.id = ?
            """, (npc_id,))
            updated = cursor.fetchone()
            
            # Format response
            npc_data = {
                "id": updated["id"],
                "npcId": updated["npc_id"],
                "displayName": updated["display_name"],
                "assetId": updated["asset_id"],
                "assetName": updated["asset_name"],
                "model": updated["model"],
                "personality": updated["system_prompt"],
                "systemPrompt": updated["system_prompt"],
                "responseRadius": updated["response_radius"],
                "spawnPosition": json.loads(updated["spawn_position"]) if updated["spawn_position"] else {},
                "abilities": json.loads(updated["abilities"]) if updated["abilities"] else [],
                "imageUrl": updated["image_url"]
            }
            
            return JSONResponse(npc_data)
    except Exception as e:
        logger.error(f"Error updating NPC: {str(e)}")
        return JSONResponse({"error": "Failed to update NPC"}, status_code=500)

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

@router.post("/api/assets/create")
async def create_asset(
    request: Request,
    game_id: int = Form(...),
    asset_id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        logger.info(f"Creating asset for game {game_id}")
        
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
            
            # Save file
            game_paths = get_game_paths(game_slug)
            asset_type_dir = type.lower() + 's'
            asset_dir = game_paths['assets'] / asset_type_dir
            asset_dir.mkdir(parents=True, exist_ok=True)
            file_path = asset_dir / f"{asset_id}.rbxm"

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
            
            # Create new database entry
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
    abilities: str = Form("[]")  # JSON string of abilities array
):
    try:
        logger.info(f"Creating NPC for game {game_id}")
        
        # Create spawn position JSON
        spawn_position = json.dumps({
            "x": spawnX,
            "y": spawnY,
            "z": spawnZ
        })
        
        # Validate abilities JSON
        try:
            abilities_list = json.loads(abilities)
            if not isinstance(abilities_list, list):
                abilities = "[]"
        except:
            abilities = "[]"
        
        with get_db() as db:
            # First check if game exists
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")

            # Generate a unique NPC ID
            npc_id = str(uuid.uuid4())
            
            # Create NPC record
            cursor.execute("""
                INSERT INTO npcs (
                    game_id,
                    npc_id,
                    display_name,
                    asset_id,
                    system_prompt,
                    response_radius,
                    spawn_position,
                    abilities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (
                game_id,
                npc_id,
                displayName,
                assetID,
                system_prompt,
                responseRadius,
                spawn_position,
                abilities  # Use the abilities JSON string
            ))
            db_id = cursor.fetchone()['id']
            db.commit()
            
            logger.info(f"NPC created successfully with ID: {db_id}")
            
            return JSONResponse({
                "id": db_id,
                "npc_id": npc_id,
                "display_name": displayName,
                "asset_id": assetID,
                "message": "NPC created successfully"
            })
            
    except Exception as e:
        logger.error(f"Error creating NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/npcs/{npc_id}")
async def delete_npc(npc_id: str, game_id: int):
    try:
        logger.info(f"Deleting NPC {npc_id} from game {game_id}")
        
        with get_db() as db:
            # Get NPC info first
            cursor = db.execute("""
                SELECT n.*, g.slug 
                FROM npcs n
                JOIN games g ON n.game_id = g.id
                WHERE n.npc_id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            npc = cursor.fetchone()
            
            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Delete the database entry
            cursor.execute("""
                DELETE FROM npcs 
                WHERE npc_id = ? AND game_id = ?
            """, (npc_id, game_id))
            
            db.commit()
            
        return JSONResponse({"message": "NPC deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update the dashboard_new route
@router.get("/dashboard/new")
async def dashboard_new(request: Request):
    """Render the new version of the dashboard"""
    return templates.TemplateResponse(
        "dashboard_new.html", 
        {"request": request}  # Jinja2Templates requires the request object
    )

# ... rest of your existing routes ...



