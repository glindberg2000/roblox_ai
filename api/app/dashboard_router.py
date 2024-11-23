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
from .utils import (
    load_json_database, 
    save_json_database, 
    save_lua_database, 
    get_database_paths,
    ensure_game_directories
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
        
        logger.info(f"Creating game with title: {data['title']}, slug: {game_slug}")
        
        try:
            # Create game directories from new template
            logger.info("About to call ensure_game_directories")
            paths = ensure_game_directories(game_slug)
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
                    
                    # Update project.json name
                    project_file = paths['root'] / "default.project.json"
                    if project_file.exists():
                        with open(project_file, 'r') as f:
                            project_data = json.load(f)
                        project_data['name'] = data['title']
                        with open(project_file, 'w') as f:
                            json.dump(project_data, f, indent=2)
                        logger.info("Updated project.json")
                    
                    # Initialize empty databases
                    save_lua_database(paths['data'] / "NPCDatabase.lua", {"npcs": []})
                    save_lua_database(paths['data'] / "AssetDatabase.lua", {"assets": []})
                    logger.info("Initialized empty databases")
                    
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
async def list_assets(game_id: Optional[int] = None, type: Optional[str] = None):
    try:
        with get_db() as db:
            logger.info(f"Fetching assets for game_id: {game_id}, type: {type}")

            # Build query based on game_id and type
            if game_id and type:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id AND n.game_id = a.game_id
                    WHERE a.game_id = ? AND a.type = ?
                    GROUP BY a.id, a.asset_id
                    ORDER BY a.name
                """, (game_id, type))
            elif game_id:
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
            npcs = get_valid_npcs(db, game_id)
            logger.info(f"Found {len(npcs)} valid NPCs")
            
            # Format the response
            formatted_npcs = [{
                "id": npc["id"],
                "npcId": npc["npc_id"],
                "displayName": npc["display_name"],
                "assetId": npc["asset_id"],
                "assetName": npc["asset_name"],
                "systemPrompt": npc["system_prompt"],
                "responseRadius": npc["response_radius"],
                "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                "imageUrl": npc["image_url"]
            } for npc in npcs]
            
            return JSONResponse({"npcs": formatted_npcs})
    except Exception as e:
        logger.error(f"Error fetching NPCs: {str(e)}")
        return JSONResponse({"error": "Failed to fetch NPCs"}, status_code=500)

@router.put("/api/games/{game_id}/assets/{asset_id}")
async def update_asset(game_id: int, asset_id: str, request: Request):
    try:
        data = await request.json()
        logger.info(f"Updating asset {asset_id} for game {game_id} with data: {data}")
        
        with get_db() as db:
            try:
                # First get game info
                cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
                game = cursor.fetchone()
                if not game:
                    raise HTTPException(status_code=404, detail="Game not found")
                
                game_slug = game['slug']
                
                # Update asset in database
                cursor.execute("""
                    UPDATE assets 
                    SET name = ?,
                        description = ?
                    WHERE game_id = ? AND asset_id = ?
                    RETURNING *
                """, (
                    data['name'],
                    data['description'],
                    game_id,
                    asset_id
                ))
                
                updated = cursor.fetchone()
                if not updated:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                # Update Lua files - pass game_slug instead of file path
                save_lua_database(game_slug, db)
                
                db.commit()
                
                # Format response
                asset_data = {
                    "id": updated["id"],
                    "assetId": updated["asset_id"],
                    "name": updated["name"],
                    "description": updated["description"],
                    "type": updated["type"],
                    "imageUrl": updated["image_url"],
                    "tags": json.loads(updated["tags"]) if updated["tags"] else []
                }
                
                return JSONResponse(asset_data)
                
            except Exception as e:
                db.rollback()
                logger.error(f"Database error updating asset: {str(e)}")
                raise
            
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
            
            # Format response
            npc_data = {
                "id": npc["id"],
                "npcId": npc["npc_id"],
                "displayName": npc["display_name"],
                "assetId": npc["asset_id"],
                "assetName": npc["asset_name"],
                "systemPrompt": npc["system_prompt"],
                "responseRadius": npc["response_radius"],
                "spawnPosition": json.loads(npc["spawn_position"]) if npc["spawn_position"] else {},
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
    """Update an NPC"""
    try:
        data = await request.json()
        logger.info(f"Updating NPC {npc_id} for game {game_id}")
        logger.info(f"Update data: {data}")
        
        # Handle spawn position - use spawnPosition field directly
        spawn_position = json.dumps(data.get('spawnPosition', {"x": 0, "y": 5, "z": 0}))
        
        with get_db() as db:
            # Get game info first
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            
            game_slug = game['slug']
            
            # Update NPC
            cursor = db.execute("""
                UPDATE npcs 
                SET display_name = ?,
                    asset_id = ?,
                    system_prompt = ?,
                    response_radius = ?,
                    abilities = ?,
                    spawn_position = ?
                WHERE npc_id = ? AND game_id = ?
                RETURNING *
            """, (
                data['displayName'],
                data['assetId'],
                data.get('systemPrompt', ''),
                data.get('responseRadius', 20),
                json.dumps(data.get('abilities', [])),
                spawn_position,
                npc_id,
                game_id
            ))
            
            updated = cursor.fetchone()
            if not updated:
                logger.error("NPC update failed - no rows returned")
                raise HTTPException(status_code=404, detail="NPC not found")
            
            logger.info(f"Updated NPC: {updated}")
            
            # Update Lua files
            save_lua_database(game_slug, db)
            
            # Format response
            response_data = {
                "id": updated["id"],
                "npcId": updated["npc_id"],
                "displayName": updated["display_name"],
                "assetId": updated["asset_id"],
                "systemPrompt": updated["system_prompt"],
                "responseRadius": updated["response_radius"],
                "abilities": json.loads(updated["abilities"]) if updated["abilities"] else [],
                "spawnPosition": json.loads(spawn_position)
            }
            
            return JSONResponse(response_data)
            
    except sqlite3.Error as e:
        logger.error(f"Database error updating NPC: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
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
            
            # Update Lua files
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
        
        # Get game info first
        with get_db() as db:
            cursor = db.execute("SELECT slug FROM games WHERE id = ?", (game_id,))
            game = cursor.fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")
            
            game_slug = game['slug']  # Get game_slug here
            
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
                abilities
            ))
            db_id = cursor.fetchone()['id']
            
            # Update Lua files
            save_lua_database(game_slug, db)
            
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

# ... rest of your existing routes ...



