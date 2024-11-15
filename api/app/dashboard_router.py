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
from slugify import slugify as python_slugify
from .utils import load_json_database, save_json_database, save_lua_database, get_database_paths
from .storage import FileStorageManager
from .image_utils import get_asset_description
from .config import STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR
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

logger = logging.getLogger("roblox_app")
router = APIRouter()

DB_PATHS = get_database_paths()

def slugify(text):
    """Wrapper around python_slugify to ensure consistent slug generation"""
    return python_slugify(text, separator='-', lowercase=True)

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
async def get_game_by_slug(slug: str):
    try:
        game = fetch_game(slug)  # Using non-async version
        if not game:
            return JSONResponse({"error": "Game not found"}, status_code=404)
        
        game_data = {
            'id': game['id'],
            'title': game['title'],
            'slug': game['slug'],
            'description': game['description'],
            'asset_count': count_assets(game['id']),
            'npc_count': count_npcs(game['id'])
        }
        return JSONResponse(game_data)
    except Exception as e:
        logger.error(f"Error fetching game: {str(e)}")
        return JSONResponse({"error": "Failed to fetch game"}, status_code=500)

@router.post("/api/games")
async def create_game_endpoint(request: Request):
    try:
        data = await request.json()
        game_slug = slugify(data['title'])
        
        try:
            game_id = create_game(data['title'], game_slug, data['description'])
            return JSONResponse({
                "id": game_id,
                "slug": game_slug,
                "message": "Game created successfully"
            })
        except Exception as e:
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
        delete_game(slug)  # Using non-async version
        return JSONResponse({"message": "Game deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting game: {str(e)}")
        return JSONResponse({"error": "Failed to delete game"}, status_code=500)

@router.get("/api/assets")
async def list_assets(game_id: Optional[int] = None):
    try:
        with get_db() as db:
            if game_id:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id
                    WHERE a.game_id = ?
                    GROUP BY a.id
                    ORDER BY a.name
                """, (game_id,))
            else:
                cursor = db.execute("""
                    SELECT a.*, COUNT(n.id) as npc_count
                    FROM assets a
                    LEFT JOIN npcs n ON a.asset_id = n.asset_id
                    GROUP BY a.id
                    ORDER BY a.name
                """)
            assets = [dict(row) for row in cursor.fetchall()]
            
            # Format the response to match expected structure
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
                    "npcCount": asset["npc_count"]
                })
            
            return JSONResponse({"assets": formatted_assets})
    except Exception as e:
        logger.error(f"Error fetching assets: {str(e)}")
        return JSONResponse({"error": "Failed to fetch assets"}, status_code=500)

@router.get("/api/npcs")
async def list_npcs(game_id: Optional[int] = None):
    try:
        with get_db() as db:
            # First, let's log what's in the database
            cursor = db.execute("SELECT * FROM npcs")
            all_npcs = cursor.fetchall()
            logger.info(f"Raw NPCs in database: {[dict(npc) for npc in all_npcs]}")
            
            if game_id:
                cursor = db.execute("""
                    SELECT 
                        n.*,
                        a.name as asset_name,
                        a.image_url,
                        n.system_prompt as personality
                    FROM npcs n
                    JOIN assets a ON n.asset_id = a.asset_id
                    WHERE n.game_id = ?
                    ORDER BY n.display_name
                """, (game_id,))
            else:
                cursor = db.execute("""
                    SELECT 
                        n.*,
                        a.name as asset_name,
                        a.image_url,
                        n.system_prompt as personality
                    FROM npcs n
                    JOIN assets a ON n.asset_id = a.asset_id
                    ORDER BY n.display_name
                """)
            npcs = [dict(row) for row in cursor.fetchall()]
            logger.info(f"NPCs after join: {npcs}")
            
            # Format the response to match expected structure
            formatted_npcs = []
            for npc in npcs:
                npc_data = {
                    "id": npc["id"],
                    "npcId": npc["npc_id"],
                    "displayName": npc["display_name"],
                    "assetId": npc["asset_id"],
                    "assetName": npc["asset_name"],
                    "model": npc["model"],
                    "personality": npc["system_prompt"],  # Use system_prompt for personality
                    "systemPrompt": npc["system_prompt"],
                    "responseRadius": npc["response_radius"],
                    "spawnPosition": json.loads(npc["spawn_position"]) if npc["spawn_position"] else {},
                    "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                    "imageUrl": npc["image_url"]
                }
                formatted_npcs.append(npc_data)
                logger.info(f"Formatted NPC data: {npc_data}")
            
            return JSONResponse({"npcs": formatted_npcs})
    except Exception as e:
        logger.error(f"Error fetching NPCs: {str(e)}")
        return JSONResponse({"error": "Failed to fetch NPCs"}, status_code=500)

@router.put("/api/assets/{asset_id}")
async def update_asset(asset_id: str, request: Request):
    try:
        data = await request.json()
        with get_db() as db:
            # Update asset in database
            db.execute("""
                UPDATE assets 
                SET name = ?, description = ?
                WHERE asset_id = ?
            """, (data['name'], data['description'], asset_id))
            
            # Get updated asset
            cursor = db.execute("""
                SELECT * FROM assets WHERE asset_id = ?
            """, (asset_id,))
            updated = cursor.fetchone()
            
            if not updated:
                return JSONResponse({"error": "Asset not found"}, status_code=404)
            
            db.commit()

            # Update JSON/Lua files
            asset_database = load_json_database(DB_PATHS['asset']['json'])
            for asset in asset_database["assets"]:
                if asset["assetId"] == asset_id:
                    asset["name"] = data['name']
                    asset["description"] = data['description']
                    break
            
            save_json_database(DB_PATHS['asset']['json'], asset_database)
            save_lua_database(DB_PATHS['asset']['lua'], asset_database)
            
            return JSONResponse(dict(updated))
    except Exception as e:
        logger.error(f"Error updating asset: {str(e)}")
        return JSONResponse({"error": "Failed to update asset"}, status_code=500)

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
        logger.info(f"Updating NPC {npc_id} with data: {data}")  # Add logging
        
        with get_db() as db:
            # Update NPC in database
            db.execute("""
                UPDATE npcs 
                SET display_name = ?,
                    asset_id = ?,
                    model = ?,
                    system_prompt = ?,  -- Store personality in system_prompt
                    response_radius = ?,
                    spawn_position = ?,
                    abilities = ?
                WHERE id = ?
            """, (
                data['displayName'],
                data['assetId'],
                data.get('model', ''),
                data.get('personality', ''),  # Use personality field for system_prompt
                data.get('responseRadius', 20),
                json.dumps(data.get('spawnPosition', {})),
                json.dumps(data.get('abilities', [])),
                npc_id
            ))
            
            # Get updated NPC with asset info
            cursor = db.execute("""
                SELECT n.*, a.name as asset_name, a.image_url,
                       n.system_prompt as personality
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.id = ?
            """, (npc_id,))
            updated = cursor.fetchone()
            
            if not updated:
                return JSONResponse({"error": "NPC not found"}, status_code=404)
            
            db.commit()
            
            # Update JSON/Lua files
            npc_database = load_json_database(DB_PATHS['npc']['json'])
            for npc in npc_database["npcs"]:
                if npc["id"] == npc_id:
                    npc["displayName"] = data['displayName']
                    npc["assetId"] = data['assetId']
                    npc["model"] = data.get('model', '')
                    npc["system_prompt"] = data.get('personality', '')  # Use personality field
                    npc["responseRadius"] = data.get('responseRadius', 20)
                    npc["spawnPosition"] = data.get('spawnPosition', {})
                    npc["abilities"] = data.get('abilities', [])
                    break
            
            save_json_database(DB_PATHS['npc']['json'], npc_database)
            save_lua_database(DB_PATHS['npc']['lua'], npc_database)
            
            # Format response
            npc_data = {
                "id": updated["id"],
                "npcId": updated["npc_id"],
                "displayName": updated["display_name"],
                "assetId": updated["asset_id"],
                "assetName": updated["asset_name"],
                "model": updated["model"],
                "personality": updated["system_prompt"],  # Use system_prompt as personality
                "systemPrompt": updated["system_prompt"],
                "responseRadius": updated["response_radius"],
                "spawnPosition": json.loads(updated["spawn_position"]) if updated["spawn_position"] else {},
                "abilities": json.loads(updated["abilities"]) if updated["abilities"] else [],
                "imageUrl": updated["image_url"]
            }
            
            logger.info(f"Updated NPC data: {npc_data}")  # Add logging
            return JSONResponse(npc_data)
    except Exception as e:
        logger.error(f"Error updating NPC: {str(e)}")
        return JSONResponse({"error": "Failed to update NPC"}, status_code=500)

# ... rest of your existing routes ...



