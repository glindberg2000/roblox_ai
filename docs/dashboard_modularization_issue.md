
Problem Description: NPC Edit Form Issue in New Dashboard

Current State:
1. NPC edit form is showing empty values for required fields
2. Save operation fails with 500 Internal Server Error
3. Error message: "'NoneType' object is not subscriptable"

Relevant Logs:

### api/app/dashboard_router.py
```javascript
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
async def update_npc(npc_id: str, game_id: int, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating NPC {npc_id} with data: {data}")
        
        with get_db() as db:
            # First verify the NPC exists
            cursor = db.execute("""
                SELECT n.*, g.slug 
                FROM npcs n
                JOIN games g ON n.game_id = g.id
                WHERE n.id = ? AND n.game_id = ?
            """, (npc_id, game_id))
            npc = cursor.fetchone()
            
            if not npc:
                logger.error(f"NPC not found: {npc_id}")
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Update NPC in database
            cursor.execute("""
                UPDATE npcs 
                SET display_name = ?,
                    asset_id = ?,
                    system_prompt = ?,
                    response_radius = ?,
                    abilities = ?
                WHERE id = ? AND game_id = ?
            """, (
                data['displayName'],
                data['assetId'],
                data['systemPrompt'],
                data['responseRadius'],
                json.dumps(data['abilities']),
                npc_id,
                game_id
            ))
            
            db.commit()
            
            # Get updated NPC data
            cursor.execute("""
                SELECT n.*, a.name as asset_name, a.image_url
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id AND a.game_id = n.game_id
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
                "systemPrompt": updated["system_prompt"],
                "responseRadius": updated["response_radius"],
                "abilities": json.loads(updated["abilities"]) if updated["abilities"] else [],
                "imageUrl": updated["image_url"]
            }
            
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




```

### api/static/js/dashboard_new/index.js
```javascript
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentTab } from './state.js';
import { loadGames } from './games.js';

console.log('Loading NEW dashboard version');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing dashboard...');
    await loadGames();
});

// Add populateAssetSelector function
async function populateAssetSelector() {
    if (!state.currentGame) {
        console.log('No game selected for asset selector');
        return;
    }

    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        
        const assetSelect = document.getElementById('assetSelect');
        if (assetSelect) {
            // Clear existing options
            assetSelect.innerHTML = '<option value="">Select an asset...</option>';
            
            // Add options for each asset
            if (data.assets && Array.isArray(data.assets)) {
                data.assets.forEach(asset => {
                    const option = document.createElement('option');
                    option.value = asset.assetId;
                    option.textContent = asset.name;
                    assetSelect.appendChild(option);
                });
            }
            console.log('Populated asset selector with', data.assets?.length || 0, 'assets');
        }
    } catch (error) {
        console.error('Error loading assets for selector:', error);
        showNotification('Failed to load assets for selection', 'error');
    }
}

// Tab management
window.showTab = function(tabName) {
    console.log('Showing tab:', tabName);
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    updateCurrentTab(tabName);

    if (tabName === 'games') {
        loadGames();
    } else if (tabName === 'assets' && state.currentGame) {
        window.loadAssets();
    } else if (tabName === 'npcs' && state.currentGame) {
        window.loadNPCs();
        populateAssetSelector();
    }
};

// Make populateAssetSelector globally available
window.populateAssetSelector = populateAssetSelector;








```

### api/static/js/dashboard_new/state.js
```javascript
// Centralized state management
export const state = {
    currentGame: null,
    currentTab: 'games',
    currentAssets: [],
    currentNPCs: []
};

// State update functions
export function updateCurrentGame(game) {
    state.currentGame = game;
    // Update UI
    const display = document.getElementById('currentGameDisplay');
    if (display) {
        display.textContent = `Current Game: ${game.title}`;
    }
}

export function updateCurrentTab(tab) {
    state.currentTab = tab;
}

export function updateCurrentAssets(assets) {
    state.currentAssets = assets;
}

export function updateCurrentNPCs(npcs) {
    state.currentNPCs = npcs;
}

export function resetState() {
    state.currentGame = null;
    state.currentAssets = [];
    state.currentNPCs = [];
} 
```

### api/static/js/dashboard_new/ui.js
```javascript
import { state } from './state.js';

export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'error' ? 'bg-red-600' :
        type === 'success' ? 'bg-green-600' :
        'bg-blue-600'
    } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 3000);
    }, 3000);
}

export function showModal(content) {
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';

    const modal = document.createElement('div');
    modal.className = 'bg-dark-900 rounded-lg shadow-xl max-w-2xl w-full mx-4';

    const closeButton = document.createElement('button');
    closeButton.className = 'absolute top-4 right-4 text-gray-400 hover:text-white';
    closeButton.innerHTML = '<i class="fas fa-times"></i>';
    closeButton.onclick = hideModal;

    modal.appendChild(closeButton);
    modal.appendChild(content);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    document.body.style.overflow = 'hidden';
}

export function hideModal() {
    const modal = document.querySelector('.fixed.inset-0');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

export function closeAssetEditModal() {
    const modal = document.getElementById('assetEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

export function closeNPCEditModal() {
    const modal = document.getElementById('npcEditModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Make modal functions globally available
window.showModal = showModal;
window.hideModal = hideModal;
window.closeAssetEditModal = closeAssetEditModal;
window.closeNPCEditModal = closeNPCEditModal; 
```

### api/static/js/dashboard_new/utils.js
```javascript
export function debugLog(title, data) {
    // You can set this to false in production
    const DEBUG = true;
    
    if (DEBUG) {
        console.log(`=== ${title} ===`);
        console.log(JSON.stringify(data, null, 2));
        console.log('=================');
    }
}

export function validateData(data, schema) {
    // Basic data validation helper
    for (const [key, requirement] of Object.entries(schema)) {
        if (requirement.required && !data[key]) {
            throw new Error(`Missing required field: ${key}`);
        }
    }
    return true;
}

// Make debug functions globally available if needed
window.debugLog = debugLog;

export function validateAsset(data) {
    const required = ['name', 'assetId', 'type'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    return true;
}

export function validateNPC(data) {
    const required = ['displayName', 'assetId', 'systemPrompt'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    return true;
}
```

### api/static/js/dashboard_new/games.js
```javascript
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state, updateCurrentGame } from './state.js';

// Export game-related functions
export async function loadGames() {
    console.log('Loading games...');
    try {
        const response = await fetch('/api/games');
        const games = await response.json();
        console.log('Loaded games:', games);

        const gamesContainer = document.getElementById('games-container');
        if (!gamesContainer) {
            console.error('games-container element not found!');
            return;
        }

        gamesContainer.innerHTML = '';

        games.forEach(game => {
            console.log('Creating card for game:', game);
            const gameCard = document.createElement('div');
            gameCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            gameCard.innerHTML = `
                <h3 class="text-xl font-bold text-gray-100 mb-2">${game.title}</h3>
                <p class="text-gray-400 mb-4">${game.description || 'No description'}</p>
                <div class="flex items-center text-sm text-gray-400 mb-4">
                    <span class="mr-4"><i class="fas fa-cube"></i> Assets: ${game.asset_count || 0}</span>
                    <span><i class="fas fa-user"></i> NPCs: ${game.npc_count || 0}</span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="window.selectGame('${game.slug}')" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200">
                        <i class="fas fa-check-circle"></i> Select
                    </button>
                    <button onclick="window.editGame('${game.slug}')" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="window.deleteGame('${game.slug}')" 
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            `;
            gamesContainer.appendChild(gameCard);
            console.log('Added game card:', game.title);
        });
    } catch (error) {
        console.error('Error loading games:', error);
        showNotification('Failed to load games', 'error');
    }
}

export async function selectGame(gameSlug) {
    try {
        debugLog('Selecting game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`);

        if (!response.ok) {
            throw new Error(`Failed to select game: ${response.statusText}`);
        }

        const game = await response.json();
        updateCurrentGame(game);  // Use state management function
        console.log('Game selected:', game);

        showNotification(`Selected game: ${game.title}`, 'success');

        // Stay on current tab and refresh data
        if (state.currentTab === 'assets') {
            window.loadAssets();
        } else if (state.currentTab === 'npcs') {
            window.loadNPCs();
            window.populateAssetSelector();
        }

    } catch (error) {
        console.error('Error selecting game:', error);
        showNotification(`Failed to select game: ${error.message}`, 'error');
    }
}

export async function editGame(gameSlug) {
    try {
        debugLog('Editing game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`);
        const game = await response.json();

        const modalContent = document.createElement('div');
        modalContent.className = 'p-6';
        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Game</h2>
            </div>
            <form id="edit-game-form" class="space-y-4">
                <input type="hidden" id="edit-game-slug" value="${gameSlug}">
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Title</label>
                    <input type="text" id="edit-game-title" value="${game.title}" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description</label>
                    <textarea id="edit-game-description" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${game.description || ''}</textarea>
                </div>
            </form>
        `;

        showModal(modalContent);

        // Add form submit handler
        const form = modalContent.querySelector('form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            await saveGameEdit(gameSlug);
        };

    } catch (error) {
        console.error('Error editing game:', error);
        showNotification('Failed to edit game', 'error');
    }
}

export async function saveGameEdit(gameSlug) {
    try {
        const title = document.getElementById('edit-game-title').value;
        const description = document.getElementById('edit-game-description').value;

        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, description })
        });

        if (!response.ok) {
            throw new Error('Failed to update game');
        }

        hideModal();
        showNotification('Game updated successfully', 'success');
        loadGames();
    } catch (error) {
        console.error('Error saving game:', error);
        showNotification('Failed to save changes', 'error');
    }
}

export async function deleteGame(gameSlug) {
    if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
        return;
    }

    try {
        debugLog('Deleting game', { gameSlug });
        const response = await fetch(`/api/games/${gameSlug}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete game');
        }

        showNotification('Game deleted successfully', 'success');
        loadGames();
    } catch (error) {
        console.error('Error deleting game:', error);
        showNotification('Failed to delete game', 'error');
    }
}

// Make functions globally available
window.loadGames = loadGames;
window.selectGame = selectGame;
window.editGame = editGame;
window.deleteGame = deleteGame; 
```

### api/static/js/dashboard_new/assets.js
```javascript
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

export async function loadAssets() {
    if (!state.currentGame) {
        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading assets for game', {
            gameId: state.currentGame.id,
            gameSlug: state.currentGame.slug
        });

        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}`);
        const data = await response.json();
        state.currentAssets = data.assets;
        debugLog('Loaded Assets', state.currentAssets);

        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '';

        if (!state.currentAssets || state.currentAssets.length === 0) {
            assetList.innerHTML = '<p class="text-gray-400 text-center p-4">No assets found for this game</p>';
            return;
        }

        state.currentAssets.forEach(asset => {
            const assetCard = document.createElement('div');
            assetCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            assetCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    <img src="${asset.imageUrl}" 
                         alt="${asset.name}" 
                         class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                </div>
                <h3 class="font-bold text-lg truncate text-gray-100">${asset.name}</h3>
                <p class="text-sm text-gray-400 mb-2">ID: ${asset.assetId}</p>
                <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${asset.description || 'No description'}</p>
                <div class="flex space-x-2">
                    <button onclick="window.editAsset('${asset.assetId}')" 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="window.deleteAsset('${asset.assetId}')" 
                            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>
            `;
            assetList.appendChild(assetCard);
        });
    } catch (error) {
        console.error('Error loading assets:', error);
        showNotification('Failed to load assets', 'error');
        const assetList = document.getElementById('assetList');
        assetList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading assets</p>';
    }
}

export async function editAsset(assetId) {
    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const asset = state.currentAssets.find(a => a.assetId === assetId);
    if (!asset) {
        showNotification('Asset not found', 'error');
        return;
    }

    const modalContent = document.createElement('div');
    modalContent.className = 'p-6';
    modalContent.innerHTML = `
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-blue-400">Edit Asset</h2>
        </div>
        <form id="editAssetForm" class="space-y-4">
            <input type="hidden" id="editAssetId" value="${asset.assetId}">
            
            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                <input type="text" id="editAssetName" value="${asset.name}" required
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
            </div>

            <div>
                <div class="flex items-center space-x-2 mb-1">
                    <label class="block text-sm font-medium text-gray-300">Current Image:</label>
                    <span id="editAssetId_display" class="text-sm text-gray-400">${asset.assetId}</span>
                </div>
                <img src="${asset.imageUrl}" alt="${asset.name}"
                    class="w-full h-48 object-contain rounded-lg border border-dark-600 bg-dark-700 mb-4">
            </div>

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                <textarea id="editAssetDescription" required rows="4"
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${asset.description || ''}</textarea>
            </div>

            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="window.hideModal()" 
                    class="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600">
                    Cancel
                </button>
                <button type="submit" 
                    class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Save Changes
                </button>
            </div>
        </form>
    `;

    showModal(modalContent);

    // Add form submit handler
    const form = modalContent.querySelector('form');
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveAssetEdit(assetId);
    };
}

export async function saveAssetEdit(assetId) {
    try {
        const form = document.getElementById('editAssetForm');
        const data = {
            name: document.getElementById('editAssetName').value,
            description: document.getElementById('editAssetDescription').value
        };

        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to update asset');
        }

        hideModal();
        showNotification('Asset updated successfully', 'success');
        loadAssets();  // Refresh the list
    } catch (error) {
        console.error('Error saving asset:', error);
        showNotification('Failed to save changes', 'error');
    }
}

export async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset?')) {
        return;
    }

    try {
        const response = await fetch(`/api/games/${state.currentGame.id}/assets/${assetId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete asset');
        }

        showNotification('Asset deleted successfully', 'success');
        loadAssets();
    } catch (error) {
        console.error('Error deleting asset:', error);
        showNotification('Failed to delete asset', 'error');
    }
}

export async function createAsset(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const submitBtn = document.getElementById('submitAssetBtn');
    submitBtn.disabled = true;

    try {
        const formData = new FormData(event.target);
        formData.set('game_id', state.currentGame.id);

        debugLog('Submitting asset form with data:', {
            game_id: formData.get('game_id'),
            asset_id: formData.get('asset_id'),
            name: formData.get('name'),
            type: formData.get('type'),
            file: formData.get('file').name
        });

        const response = await fetch('/api/assets/create', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create asset');
        }

        const result = await response.json();
        console.log('Asset created:', result);

        showNotification('Asset created successfully', 'success');
        event.target.reset();
        loadAssets();

    } catch (error) {
        console.error('Error creating asset:', error);
        showNotification(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
    }
}

// Make functions globally available
window.loadAssets = loadAssets;
window.editAsset = editAsset;
window.deleteAsset = deleteAsset;
window.createAsset = createAsset; 
```

### api/static/js/dashboard_new/npc.js
```javascript
import { showNotification } from './ui.js';
import { debugLog } from './utils.js';
import { state } from './state.js';

export async function loadNPCs() {
    if (!state.currentGame) {
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-gray-400 text-center p-4">Please select a game first</p>';
        return;
    }

    try {
        debugLog('Loading NPCs for game', {
            gameId: state.currentGame.id,
            gameSlug: state.currentGame.slug
        });

        const response = await fetch(`/api/npcs?game_id=${state.currentGame.id}`);
        const data = await response.json();
        state.currentNPCs = data.npcs;
        debugLog('Loaded NPCs', state.currentNPCs);

        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '';

        if (!state.currentNPCs || state.currentNPCs.length === 0) {
            npcList.innerHTML = '<p class="text-gray-400 text-center p-4">No NPCs found for this game</p>';
            return;
        }

        state.currentNPCs.forEach(npc => {
            const npcCard = document.createElement('div');
            npcCard.className = 'bg-dark-800 p-6 rounded-xl shadow-xl border border-dark-700 hover:border-blue-500 transition-colors duration-200';
            npcCard.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 mb-4">
                    <img src="${npc.imageUrl || ''}" 
                         alt="${npc.displayName}" 
                         class="w-full h-32 object-contain rounded-lg bg-dark-700 p-2">
                </div>
                <h3 class="font-bold text-lg truncate text-gray-100">${npc.displayName}</h3>
                <p class="text-sm text-gray-400 mb-2">Asset ID: ${npc.assetId}</p>
                <p class="text-sm text-gray-400 mb-2">Model: ${npc.model || 'Default'}</p>
                <p class="text-sm mb-4 h-20 overflow-y-auto text-gray-300">${npc.systemPrompt || 'No personality defined'}</p>
                <div class="text-sm text-gray-400 mb-4">
                    <div>Response Radius: ${npc.responseRadius}m</div>
                    <div>Abilities: ${(npc.abilities || []).join(', ') || 'None'}</div>
                </div>
                <div class="flex space-x-2">
                    <button onclick="window.editNPC('${npc.npcId}')" 
                            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Edit
                    </button>
                    <button onclick="window.deleteNPC('${npc.npcId}')" 
                            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>
            `;
            npcList.appendChild(npcCard);
        });
    } catch (error) {
        console.error('Error loading NPCs:', error);
        showNotification('Failed to load NPCs', 'error');
        const npcList = document.getElementById('npcList');
        npcList.innerHTML = '<p class="text-red-400 text-center p-4">Error loading NPCs</p>';
    }
}

// Add this function to fetch available models
async function fetchAvailableModels() {
    try {
        const response = await fetch(`/api/assets?game_id=${state.currentGame.id}&type=NPC`);
        const data = await response.json();
        return data.assets || [];
    } catch (error) {
        console.error('Error fetching models:', error);
        return [];
    }
}

// Update the editNPC function to use models
export async function editNPC(npcId) {
    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    const npc = state.currentNPCs.find(n => n.npcId === npcId);
    if (!npc) {
        showNotification('NPC not found', 'error');
        return;
    }

    // Fetch available models
    const availableModels = await fetchAvailableModels();

    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'p-6';
    modalContent.innerHTML = `
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
        </div>
        <form id="editNPCForm" class="space-y-4">
            <input type="hidden" id="editNpcId" value="${npc.npcId}">
            
            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                <input type="text" id="editNpcDisplayName" value="${npc.displayName}" required
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
            </div>

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                <input type="number" id="editNpcRadius" value="${npc.responseRadius || 20}" required min="1" max="100"
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
            </div>

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">System Prompt:</label>
                <textarea id="editNpcPrompt" required rows="4"
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">${npc.systemPrompt || ''}</textarea>
            </div>

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                <div id="editAbilitiesContainer" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                    ${window.ABILITY_CONFIG.map(ability => `
                        <label class="flex items-center space-x-2">
                            <input type="checkbox" name="abilities" value="${ability.id}"
                                ${(npc.abilities || []).includes(ability.id) ? 'checked' : ''}
                                class="form-checkbox h-4 w-4 text-blue-600">
                            <span class="text-gray-300">
                                <i class="${ability.icon}"></i>
                                ${ability.name}
                            </span>
                        </label>
                    `).join('')}
                </div>
            </div>

            <div>
                <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                <select id="editNpcModel" required
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    ${availableModels.map(model => `
                        <option value="${model.assetId}" ${model.assetId === npc.assetId ? 'selected' : ''}>
                            ${model.name}
                        </option>
                    `).join('')}
                </select>
            </div>

            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="window.hideModal()" 
                    class="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600">
                    Cancel
                </button>
                <button type="submit" 
                    class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Save Changes
                </button>
            </div>
        </form>
    `;

    showModal(modalContent);

    // Add form submit handler
    const form = modalContent.querySelector('form');
    form.onsubmit = async (e) => {
        e.preventDefault();
        await saveNPCEdit(npcId);
    };
}

export async function saveNPCEdit(npcId) {
    try {
        const form = document.getElementById('editNPCForm');
        const selectedAbilities = Array.from(
            form.querySelectorAll('input[name="abilities"]:checked')
        ).map(checkbox => checkbox.value);

        const data = {
            displayName: document.getElementById('editNpcDisplayName').value,
            responseRadius: parseInt(document.getElementById('editNpcRadius').value),
            systemPrompt: document.getElementById('editNpcPrompt').value,
            abilities: selectedAbilities,
            assetId: document.getElementById('editNpcModel').value
        };

        // Find the NPC to get its database ID
        const npc = state.currentNPCs.find(n => n.npcId === npcId);
        if (!npc) {
            throw new Error('NPC not found');
        }

        // Use npc.id instead of npcId for the API call
        const response = await fetch(`/api/npcs/${npc.id}?game_id=${state.currentGame.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update NPC');
        }

        hideModal();
        showNotification('NPC updated successfully', 'success');
        loadNPCs();  // Refresh the list
    } catch (error) {
        console.error('Error saving NPC:', error);
        showNotification('Failed to save changes', 'error');
    }
}

// Add delete function
export async function deleteNPC(npcId) {
    if (!confirm('Are you sure you want to delete this NPC?')) {
        return;
    }

    try {
        const response = await fetch(`/api/npcs/${npcId}?game_id=${state.currentGame.id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete NPC');
        }

        showNotification('NPC deleted successfully', 'success');
        loadNPCs();
    } catch (error) {
        console.error('Error deleting NPC:', error);
        showNotification('Failed to delete NPC', 'error');
    }
}

// Make functions globally available
window.loadNPCs = loadNPCs;
window.editNPC = editNPC;
window.deleteNPC = deleteNPC;

export async function createNPC(event) {
    event.preventDefault();
    console.log('NPC form submitted');

    if (!state.currentGame) {
        showNotification('Please select a game first', 'error');
        return;
    }

    try {
        const form = event.target;
        const formData = new FormData(form);
        formData.set('game_id', state.currentGame.id);

        // Get selected abilities
        const abilities = [];
        form.querySelectorAll('input[name="abilities"]:checked').forEach(checkbox => {
            abilities.push(checkbox.value);
        });
        formData.set('abilities', JSON.stringify(abilities));

        debugLog('Submitting NPC', {
            game_id: formData.get('game_id'),
            displayName: formData.get('displayName'),
            assetID: formData.get('assetID'),
            system_prompt: formData.get('system_prompt'),
            abilities: formData.get('abilities')
        });

        const response = await fetch('/api/npcs', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create NPC');
        }

        const result = await response.json();
        console.log('NPC created:', result);

        showNotification('NPC created successfully', 'success');
        form.reset();

        // Refresh the NPCs list
        loadNPCs();

    } catch (error) {
        console.error('Error creating NPC:', error);
        showNotification(error.message, 'error');
    }
}

// Add to global window object
window.createNPC = createNPC;

// Add this function to populate abilities in the create form
function populateCreateAbilities() {
    const container = document.getElementById('createAbilitiesCheckboxes');
    if (container && window.ABILITY_CONFIG) {
        container.innerHTML = window.ABILITY_CONFIG.map(ability => `
            <label class="flex items-center space-x-2">
                <input type="checkbox" name="abilities" value="${ability.id}"
                    class="form-checkbox h-4 w-4 text-blue-600">
                <span class="text-gray-300">
                    <i class="${ability.icon}"></i>
                    ${ability.name}
                </span>
            </label>
        `).join('');
    }
}

// Update the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    populateCreateAbilities();
});
```

### api/static/js/abilityConfig.js
```javascript
const ABILITY_CONFIG = [
    {
        id: 'move',
        name: 'Movement',
        icon: 'fas fa-walking',
        description: 'Allows NPC to move around'
    },
    {
        id: 'chat',
        name: 'Chat',
        icon: 'fas fa-comments',
        description: 'Enables conversation with players'
    },
    {
        id: 'trade',
        name: 'Trading',
        icon: 'fas fa-exchange-alt',
        description: 'Allows trading items with players'
    },
    {
        id: 'quest',
        name: 'Quest Giver',
        icon: 'fas fa-scroll',
        description: 'Can give and manage quests'
    },
    {
        id: 'combat',
        name: 'Combat',
        icon: 'fas fa-sword',
        description: 'Enables combat abilities'
    }
];

window.ABILITY_CONFIG = ABILITY_CONFIG;

```

### api/templates/dashboard_new.html
```javascript
<!DOCTYPE html>
<html lang="en" class="dark">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roblox Asset Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        dark: {
                            50: '#f9fafb',
                            100: '#f3f4f6',
                            200: '#e5e7eb',
                            300: '#d1d5db',
                            400: '#9ca3af',
                            500: '#6b7280',
                            600: '#4b5563',
                            700: '#374151',
                            800: '#1f2937',
                            900: '#111827',
                        },
                    },
                },
            },
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
        }

        .modal-content {
            background-color: #1f2937;
            margin: 5% auto;
            padding: 2rem;
            border: 1px solid #374151;
            width: 90%;
            max-width: 600px;
            border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }

        .notification {
            transition: opacity 0.3s ease-in-out;
        }

        /* Modern scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1f2937;
        }

        ::-webkit-scrollbar-thumb {
            background: #4b5563;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #6b7280;
        }
    </style>
    <!-- <script src="/static/js/games.js" defer></script> -->
</head>

<body class="bg-dark-900 text-gray-100 min-h-screen font-sans">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-4xl font-bold mb-6 text-blue-400">Roblox Asset Manager (New Version)</h1>
            <div class="mb-6 bg-dark-800 p-4 rounded-xl shadow-xl">
                <div id="currentGameDisplay" class="text-xl font-semibold text-gray-300">
                    <!-- Will be populated by JS -->
                </div>
            </div>
            <div class="flex space-x-4">
                <button onclick="showTab('games')"
                    class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg">
                    <i class="fas fa-gamepad"></i> Games
                </button>
                <button onclick="showTab('assets')"
                    class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg">
                    Assets
                </button>
                <button onclick="showTab('npcs')"
                    class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg">
                    NPCs
                </button>
                <button onclick="showTab('players')"
                    class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg">
                    Players
                </button>
            </div>
        </div>

        <!-- Asset Tab -->
        <div id="assetsTab" class="tab-content">
            <div class="mb-8 bg-dark-800 p-6 rounded-xl shadow-xl">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Add New Asset</h2>
                <form id="assetForm" class="space-y-4" enctype="multipart/form-data" onsubmit="createAsset(event)">
                    <input type="hidden" name="game_id" id="assetFormGameId">
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Asset ID:</label>
                        <input type="text" name="asset_id" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                        <input type="text" name="name" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Type:</label>
                        <select name="type" required
                            class="w-full p-3 bg-dark-700 text-gray-200 rounded-lg">
                            <option value="NPC">NPC</option>
                            <option value="Vehicle">Vehicle</option>
                            <option value="Building">Building</option>
                            <option value="Prop">Prop</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Asset File (.rbxm):</label>
                        <input type="file" name="file" accept=".rbxm,.rbxmx" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    
                    <button type="submit" id="submitAssetBtn" class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Add Asset
                    </button>
                </form>
            </div>

            <div>
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Asset List</h2>
                <div id="assetList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Assets will be loaded here -->
                </div>
            </div>
        </div>

        <!-- NPCs Tab -->
        <div id="npcsTab" class="tab-content hidden">
            <div class="mb-8 bg-dark-800 p-6 rounded-xl shadow-xl">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Add New NPC</h2>
                <form id="npcForm" onsubmit="createNPC(event)" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                        <input type="text" name="displayName" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Asset:</label>
                        <select name="assetID" required 
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                            id="assetSelect">
                            <option value="">Select an asset...</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                        <input type="number" name="responseRadius" required value="20" min="1" max="100"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">System Prompt:</label>
                        <textarea name="system_prompt" required rows="4"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter the NPC's personality and behavior description..."></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Spawn Position:</label>
                        <div class="grid grid-cols-3 gap-4">
                            <div>
                                <label class="text-xs text-gray-400">X</label>
                                <input type="number" name="spawnX" value="0" required
                                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            </div>
                            <div>
                                <label class="text-xs text-gray-400">Y</label>
                                <input type="number" name="spawnY" value="5" required
                                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            </div>
                            <div>
                                <label class="text-xs text-gray-400">Z</label>
                                <input type="number" name="spawnZ" value="0" required
                                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            </div>
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2 text-gray-300">Abilities:</label>
                        <div id="createAbilitiesCheckboxes" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                            <!-- Will be populated from ABILITY_CONFIG -->
                        </div>
                    </div>
                    <button type="submit"
                        class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg">
                        Add NPC
                    </button>
                </form>
            </div>

            <div>
                <h2 class="text-2xl font-bold mb-4 text-blue-400">NPC List</h2>
                <div id="npcList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- NPCs will be loaded here -->
                </div>
            </div>
        </div>

        <!-- Players Tab -->
        <div id="playersTab" class="tab-content hidden">
            <h2 class="text-2xl font-bold mb-4 text-blue-400">Players</h2>
            <div id="playerList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Players will be loaded here -->
            </div>
        </div>

        <!-- Games Tab -->
        <div id="gamesTab" class="tab-content">
            <div>
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Game List</h2>
                <div id="games-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    <!-- Games will be loaded here -->
                </div>
            </div>

            <div class="bg-dark-800 p-6 rounded-xl shadow-xl">
                <h2 class="text-2xl font-bold mb-4 text-blue-400">Add New Game</h2>
                <form id="gameForm" onsubmit="return handleGameSubmit(event)" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Game Title:</label>
                        <input type="text" name="title" required
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                        <textarea name="description" required rows="4"
                            class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100"
                            placeholder="Enter game description..."></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1 text-gray-300">Clone From:</label>
                        <select name="cloneFrom" id="cloneFromSelect" class="w-full p-3 bg-dark-700 text-gray-200 rounded-lg">
                            <option value="">Empty Game (No Assets)</option>
                        </select>
                    </div>
                    <button type="submit"
                        class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Add Game
                    </button>
                </form>
            </div>
        </div>
    </div>

    <!-- Edit Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <h2 class="text-xl font-bold mb-4 text-blue-400">Edit Description</h2>
            <form id="editForm" onsubmit="saveEdit(event)" class="space-y-4">
                <input type="hidden" id="editItemId">
                <input type="hidden" id="editItemType">
                <textarea id="editDescription"
                    class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="6"></textarea>
                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="closeEditModal()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200">
                        Cancel
                    </button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Save
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- NPC Edit Modal -->
    <div id="npcEditModal" class="modal">
        <div class="modal-content max-w-2xl">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit NPC</h2>
                <button onclick="closeNPCEditModal()"
                    class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
            </div>
            <form id="npcEditForm" onsubmit="saveNPCEdit(event)" class="space-y-6">
                <input type="hidden" id="editNpcId">

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Display Name:</label>
                    <input type="text" id="editNpcDisplayName" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Model:</label>
                    <select id="editNpcModel" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                        <!-- Will be populated dynamically -->
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Response Radius:</label>
                    <input type="number" id="editNpcRadius" required min="1" max="100"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Personality:</label>
                    <textarea id="editNpcPrompt" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100"></textarea>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Abilities:</label>
                    <div id="editAbilitiesCheckboxes" class="grid grid-cols-2 gap-2 bg-dark-700 p-4 rounded-lg">
                        <!-- Checkboxes will be populated via JavaScript -->
                    </div>
                </div>

                <div class="flex justify-end space-x-4 pt-4">
                    <button type="button" onclick="closeNPCEditModal()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                        Cancel
                    </button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Asset Edit Modal -->
    <div id="assetEditModal" class="modal">
        <div class="modal-content max-w-2xl">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold text-blue-400">Edit Asset</h2>
                <button onclick="closeAssetEditModal()"
                    class="text-gray-400 hover:text-gray-200 text-2xl">&times;</button>
            </div>
            <form id="assetEditForm" onsubmit="saveAssetEdit(event)" class="space-y-6">
                <input type="hidden" id="editAssetId">

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Name:</label>
                    <input type="text" id="editAssetName" required
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                </div>

                <div>
                    <div class="flex items-center space-x-2 mb-1">
                        <label class="block text-sm font-medium text-gray-300">Current Image:</label>
                        <span id="editAssetId_display" class="text-sm text-gray-400"></span>
                    </div>
                    <img id="editAssetImage"
                        class="w-full h-48 object-contain rounded-lg border border-dark-600 bg-dark-700 mb-4">
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1 text-gray-300">Description:</label>
                    <textarea id="editAssetDescription" required rows="4"
                        class="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"></textarea>
                </div>

                <div class="flex justify-end space-x-4 pt-4">
                    <button type="button" onclick="closeAssetEditModal()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200">
                        Cancel
                    </button>
                    <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Add game management modal -->
    <div id="gameModal" class="modal">
        <div class="modal-content">
            <h2>Create New Game</h2>
            <form id="gameForm">
                <input type="text" name="name" placeholder="Game Name" required>
                <input type="text" name="slug" placeholder="URL Slug" required>
                <textarea name="description" placeholder="Description"></textarea>
                <button type="submit">Create Game</button>
            </form>
        </div>
    </div>

    <script src="/static/js/dashboard_new/abilityConfig.js"></script>
    <script type="module" src="/static/js/dashboard_new/utils.js"></script>
    <script type="module" src="/static/js/dashboard_new/ui.js"></script>
    <script type="module" src="/static/js/dashboard_new/state.js"></script>
    <script type="module" src="/static/js/dashboard_new/games.js"></script>
    <script type="module" src="/static/js/dashboard_new/assets.js"></script>
    <script type="module" src="/static/js/dashboard_new/npc.js"></script>
    <script type="module" src="/static/js/dashboard_new/index.js"></script>
</body>

</html>

```
