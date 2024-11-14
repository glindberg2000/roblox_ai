import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import xml.etree.ElementTree as ET
import requests
from .utils import load_json_database, save_json_database, save_lua_database, get_database_paths
from .storage import FileStorageManager
from .image_utils import get_asset_description
from .config import STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR
from .database import get_db

# Initialize logging
logger = logging.getLogger("roblox_app")
router = APIRouter()

# Get database paths
DB_PATHS = get_database_paths()

# Initialize file storage manager
file_manager = FileStorageManager()

# Pydantic Models
class AssetData(BaseModel):
    assetId: str
    name: str

class EditItemRequest(BaseModel):
    name: str
    description: str
    assetId: str

class UpdateAssetsRequest(BaseModel):
    overwrite: bool = False
    single_asset: Optional[str] = None
    only_empty: bool = False

class PlayerData(BaseModel):
    playerID: str
    displayName: str
    imageURL: Optional[str] = None
    description: Optional[str] = None

class NPCData(BaseModel):
    id: str
    displayName: str
    model: str
    responseRadius: int
    spawnPosition: Dict[str, float]
    system_prompt: str
    shortTermMemory: List[str] = []
    assetID: str

# RBXMX parsing
async def parse_rbxmx(file: UploadFile) -> Dict:
    """Parse RBXMX file to extract relevant metadata."""
    try:
        content = await file.read()
        root = ET.fromstring(content)
        
        # Find source asset ID
        source_asset_id = None
        for item in root.findall(".//SourceAssetId"):
            if item.text and item.text.strip() != "0":
                source_asset_id = item.text.strip()
                break

        # Get name from the model
        name = None
        for item in root.findall(".//Properties/string[@name='Name']"):
            name = item.text
            break

        # Find components/parts
        components = []
        for item in root.findall(".//Item"):
            class_name = item.get('class')
            if class_name and class_name not in components:
                components.append(class_name)

        return {
            "sourceAssetId": source_asset_id,
            "name": name,
            "components": components
        }
    except Exception as e:
        logger.error(f"Failed to parse RBXMX: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse RBXMX: {str(e)}")

# Asset Routes
@router.post("/api/parse-rbxmx")
async def upload_rbxmx(file: UploadFile = File(...)):
    if not file.filename.endswith('.rbxmx'):
        raise HTTPException(status_code=400, detail="File must be RBXMX format")
    
    result = await parse_rbxmx(file)
    return result

@router.post("/api/assets")
async def create_asset(
    data: str = Form(...), 
    file: Optional[UploadFile] = None,
    storage_type: str = Form(...)  # Explicit form field for storage location
):
    try:
        logger.info(f"Processing asset creation request with storage type: {storage_type}")
        asset_data = json.loads(data)
        
        # Validate storage type
        valid_types = ['npcs', 'vehicles', 'buildings', 'props']
        if storage_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid storage type. Must be one of: {valid_types}"
            )
        
        # Validate required fields
        if not asset_data.get("assetId") or not asset_data.get("name"):
            raise HTTPException(status_code=400, detail="Asset ID and name are required")

        # Get asset description and store thumbnail
        description_response = await get_asset_description(
            asset_data["assetId"],
            asset_data["name"]
        )

        # Store file if provided
        file_info = None
        if file:
            logger.info(f"Processing file upload: {file.filename}")
            try:
                file_info = await file_manager.store_asset_file(file, storage_type)
                logger.info(f"File stored successfully: {file_info}")
            except Exception as e:
                logger.error(f"Failed to store file: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

        # Create asset entry
        new_asset = {
            "assetId": asset_data["assetId"],
            "name": asset_data["name"],
            "model": asset_data.get("model") or asset_data["name"].replace(" ", ""),
            "description": description_response.get("description", ""),
            "imageUrl": description_response.get("imageUrl", ""),
            "type": asset_data.get("type", "unknown"),
            "tags": asset_data.get("tags", [])
        }

        # Load and update asset database
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        
        # Check for existing asset
        existing_asset_index = next(
            (i for i, asset in enumerate(asset_database["assets"]) 
             if asset["assetId"] == new_asset["assetId"]), 
            None
        )

        if existing_asset_index is not None:
            asset_database["assets"][existing_asset_index] = new_asset
            message = "Asset updated successfully"
        else:
            asset_database["assets"].append(new_asset)
            message = "Asset created successfully"

        # Save updated database
        save_json_database(DB_PATHS['asset']['json'], asset_database)
        save_lua_database(DB_PATHS['asset']['lua'], asset_database)

        return JSONResponse({
            "message": message,
            "asset": new_asset
        })

    except Exception as e:
        logger.error(f"Error creating asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/assets")
async def get_assets():
    """Get all assets"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT * FROM assets
            """)
            assets = cursor.fetchall()
            
            # Format response
            formatted_assets = []
            for asset in assets:
                asset_data = {
                    "assetId": asset["asset_id"],
                    "name": asset["name"],
                    "description": asset["description"],
                    "imageUrl": asset["image_url"],
                    "type": asset["type"],
                    "tags": json.loads(asset["tags"]) if asset["tags"] else []
                }
                formatted_assets.append(asset_data)
            
            return JSONResponse({"assets": formatted_assets})
            
    except Exception as e:
        logger.error(f"Error fetching asset data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/assets/{asset_id}")
async def update_asset(asset_id: str, item: EditItemRequest):
    try:
        logger.info(f"Attempting to update asset {asset_id}")
        if not asset_id:
            raise HTTPException(status_code=400, detail="Asset ID is required")
            
        # First update SQLite
        with get_db() as db:
            cursor = db.execute("""
                UPDATE assets 
                SET name = ?, description = ?
                WHERE asset_id = ?
                RETURNING *
            """, (item.name, item.description, asset_id))
            updated = cursor.fetchone()
            
            if not updated:
                raise HTTPException(status_code=404, detail="Asset not found")
                
            db.commit()
            
            # Then update JSON/Lua files
            asset_database = load_json_database(DB_PATHS['asset']['json'])
            for asset in asset_database["assets"]:
                if asset["assetId"] == asset_id:
                    asset["name"] = item.name
                    asset["description"] = item.description
                    break
                    
            save_json_database(DB_PATHS['asset']['json'], asset_database)
            save_lua_database(DB_PATHS['asset']['lua'], asset_database)
            
            return JSONResponse(dict(updated))
            
    except Exception as e:
        logger.error(f"Error updating asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: str):
    try:
        # Delete from database
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        original_length = len(asset_database["assets"])
        asset_database["assets"] = [a for a in asset_database["assets"] if a["assetId"] != asset_id]
        
        if len(asset_database["assets"]) == original_length:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Delete associated files
        await file_manager.delete_asset_files(asset_id)
            
        # Save updated database
        save_json_database(DB_PATHS['asset']['json'], asset_database)
        save_lua_database(DB_PATHS['asset']['lua'], asset_database)
        
        return JSONResponse({"message": f"Asset {asset_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete asset")

      
# NPC Routes
@router.get("/api/npcs")
async def get_npcs():
    """Get all NPCs with their asset data"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT n.*, a.image_url, a.name as asset_name
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
            """)
            npcs = cursor.fetchall()
            
            # Format response
            formatted_npcs = []
            for npc in npcs:
                npc_data = {
                    "npcId": npc["npc_id"],
                    "assetId": npc["asset_id"],
                    "displayName": npc["display_name"],
                    "description": npc["system_prompt"],
                    "system_prompt": npc["system_prompt"],
                    "imageUrl": npc["image_url"],
                    "model": npc["model"],
                    "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                    "responseRadius": npc["response_radius"],
                    "spawnPosition": json.loads(npc["spawn_position"]) if npc["spawn_position"] else {},
                }
                formatted_npcs.append(npc_data)
            
            return JSONResponse({"npcs": formatted_npcs})
            
    except Exception as e:
        logger.error(f"Error fetching NPC data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str):
    """Get a specific NPC"""
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT n.*, a.image_url 
                FROM npcs n
                JOIN assets a ON n.asset_id = a.asset_id
                WHERE n.npc_id = ?
            """, (npc_id,))
            npc = cursor.fetchone()
            
            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            return JSONResponse({
                "npcId": npc["npc_id"],
                "assetId": npc["asset_id"],
                "displayName": npc["display_name"],
                "description": npc["system_prompt"],
                "system_prompt": npc["system_prompt"],
                "imageUrl": npc["image_url"],
                "model": npc["model"],
                "abilities": json.loads(npc["abilities"]) if npc["abilities"] else [],
                "responseRadius": npc["response_radius"],
                "spawnPosition": json.loads(npc["spawn_position"]) if npc["spawn_position"] else {},
            })
            
    except Exception as e:
        logger.error(f"Error fetching NPC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/npcs/{npc_id}")
async def update_npc(npc_id: str, npc_data: dict):
    """Update an NPC"""
    try:
        logger.info(f"Attempting to update NPC {npc_id}")
        if not npc_id:
            raise HTTPException(status_code=400, detail="NPC ID is required")
            
        # First update SQLite
        with get_db() as db:
            # First verify the NPC exists
            cursor = db.execute("SELECT * FROM npcs WHERE npc_id = ?", (npc_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            # Update NPC in SQLite
            update_fields = []
            update_values = []
            
            if "displayName" in npc_data:
                update_fields.append("display_name = ?")
                update_values.append(npc_data["displayName"])
            
            if "system_prompt" in npc_data:
                update_fields.append("system_prompt = ?")
                update_values.append(npc_data["system_prompt"])
            
            if "model" in npc_data:
                update_fields.append("model = ?")
                update_values.append(npc_data["model"])
            
            if "responseRadius" in npc_data:
                update_fields.append("response_radius = ?")
                update_values.append(npc_data["responseRadius"])
            
            if "spawnPosition" in npc_data:
                update_fields.append("spawn_position = ?")
                update_values.append(json.dumps(npc_data["spawnPosition"]))
            
            if "abilities" in npc_data:
                update_fields.append("abilities = ?")
                update_values.append(json.dumps(npc_data["abilities"]))
            
            if update_fields:
                # Add npc_id to values
                update_values.append(npc_id)
                
                # Update SQLite
                query = f"""
                    UPDATE npcs 
                    SET {", ".join(update_fields)}
                    WHERE npc_id = ?
                    RETURNING *
                """
                cursor = db.execute(query, update_values)
                updated = cursor.fetchone()
                db.commit()
                
                if updated:
                    # Then update JSON/Lua files
                    npc_database = load_json_database(DB_PATHS['npc']['json'])
                    for npc in npc_database["npcs"]:
                        if npc["id"] == npc_id:
                            # Update all provided fields
                            for key, value in npc_data.items():
                                if key != "id":  # Don't change the ID
                                    npc[key] = value
                            break
                            
                    save_json_database(DB_PATHS['npc']['json'], npc_database)
                    save_lua_database(DB_PATHS['npc']['lua'], npc_database)
                    
                    return JSONResponse(dict(updated))
            
            return JSONResponse({"status": "no changes"})
            
    except Exception as e:
        logger.error(f"Error updating NPC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/npcs/{npc_id}")
async def delete_npc(npc_id: str):
    try:
        npc_database = load_json_database(DB_PATHS['npc']['json'])
        original_length = len(npc_database["npcs"])
        npc_database["npcs"] = [n for n in npc_database["npcs"] if n["id"] != npc_id]
        
        if len(npc_database["npcs"]) == original_length:
            raise HTTPException(status_code=404, detail="NPC not found")
            
        save_json_database(DB_PATHS['npc']['json'], npc_database)
        save_lua_database(DB_PATHS['npc']['lua'], npc_database)
        
        return JSONResponse({"message": f"NPC {npc_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting NPC: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete NPC")

# Add these new routes to the existing dashboard_router.py

@router.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str):
    try:
        npc_database = load_json_database(DB_PATHS['npc']['json'])
        for npc in npc_database["npcs"]:
            if npc["id"] == npc_id:
                return JSONResponse(npc)
        raise HTTPException(status_code=404, detail="NPC not found")
    except Exception as e:
        logger.error(f"Error fetching NPC: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NPC")

@router.get("/api/asset-thumbnail/{asset_id}")
async def get_asset_thumbnail(asset_id: str):
    try:
        # Use the same thumbnail fetching logic as the asset system
        asset_api_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
        response = requests.get(asset_api_url)
        response.raise_for_status()
        image_url = response.json()['data'][0]['imageUrl']
        
        return JSONResponse({
            "imageUrl": image_url
        })
    except Exception as e:
        logger.error(f"Error fetching asset thumbnail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch asset thumbnail")

# Update the existing edit_npc route to handle all fields
@router.put("/api/npcs/{npc_id}")
async def edit_npc(npc_id: str, npc_data: Dict[str, Any]):
    try:
        logger.info(f"Attempting to update NPC {npc_id}")
        if not npc_id:
            raise HTTPException(status_code=400, detail="NPC ID is required")
            
        npc_database = load_json_database(DB_PATHS['npc']['json'])
        npc_found = False
        
        for npc in npc_database["npcs"]:
            if npc["id"] == npc_id:
                npc_found = True
                
                # Update all provided fields
                for key, value in npc_data.items():
                    if key != "id":  # Don't allow ID changes
                        npc[key] = value
                
                save_json_database(DB_PATHS['npc']['json'], npc_database)
                save_lua_database(DB_PATHS['npc']['lua'], npc_database)
                
                logger.info(f"Successfully updated NPC {npc_id}")
                return JSONResponse(npc)
        
        if not npc_found:
            logger.error(f"NPC not found: {npc_id}")
            raise HTTPException(status_code=404, detail="NPC not found")
            
    except Exception as e:
        logger.error(f"Error updating NPC: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# Player Routes
@router.get("/api/players")
async def get_players():
    try:
        player_data = load_json_database(DB_PATHS['player']['json'])
        return JSONResponse({"players": player_data["players"]})
    except Exception as e:
        logger.error(f"Error fetching player data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch player data")

@router.post("/api/players")
async def add_player(player: PlayerData):
    try:
        player_database = load_json_database(DB_PATHS['player']['json'])
        player_data = player.dict()
        if not player_data["description"]:
            player_data["description"] = f"{player.displayName} is a new player in the game."
        player_database["players"].append(player_data)
        save_json_database(DB_PATHS['player']['json'], player_database)
        save_lua_database(DB_PATHS['player']['lua'], player_database)
        return JSONResponse(player_data)
    except Exception as e:
        logger.error(f"Error adding player: {e}")
        raise HTTPException(status_code=500, detail="Failed to add player")

@router.put("/api/players/{player_id}")
async def update_player(player_id: str, player: PlayerData):
    try:
        player_database = load_json_database(DB_PATHS['player']['json'])
        for idx, existing_player in enumerate(player_database["players"]):
            if existing_player["playerID"] == player_id:
                player_database["players"][idx] = player.dict()
                save_json_database(DB_PATHS['player']['json'], player_database)
                save_lua_database(DB_PATHS['player']['lua'], player_database)
                return JSONResponse(player.dict())
        raise HTTPException(status_code=404, detail="Player not found")
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        raise HTTPException(status_code=500, detail="Failed to update player")

@router.delete("/api/players/{player_id}")
async def delete_player(player_id: str):
    try:
        player_database = load_json_database(DB_PATHS['player']['json'])
        original_length = len(player_database["players"])
        player_database["players"] = [p for p in player_database["players"] if p["playerID"] != player_id]
        if len(player_database["players"]) == original_length:
            raise HTTPException(status_code=404, detail="Player not found")
        save_json_database(DB_PATHS['player']['json'], player_database)
        save_lua_database(DB_PATHS['player']['lua'], player_database)
        return JSONResponse({"message": f"Player {player_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting player: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete player")
    

# Add this new route for creating NPCs
@router.post("/api/npcs")
async def create_npc(npc_data: Dict[str, Any]):
    try:
        logger.info(f"Creating new NPC: {npc_data}")
        
        # Generate a unique ID for the new NPC
        import uuid
        npc_data["id"] = str(uuid.uuid4())
        
        # Load assets to get the linked asset data
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        
        # Find the linked asset
        asset_id = npc_data.get("assetID") or npc_data.get("assetId")
        linked_asset = next(
            (asset for asset in asset_database["assets"] 
             if asset["assetId"] == asset_id),
            None
        )
        
        if not linked_asset:
            raise HTTPException(status_code=400, detail="Invalid asset ID")
            
        # Create normalized NPC data structure
        normalized_npc = {
            "id": npc_data["id"],
            "displayName": str(npc_data["displayName"]),
            "assetId": asset_id,  # Use consistent field name
            "model": linked_asset.get("model") or npc_data["displayName"].replace(" ", ""),
            "responseRadius": int(npc_data["responseRadius"]),
            "spawnPosition": {
                "x": float(npc_data["spawnPosition"]["x"]),
                "y": float(npc_data["spawnPosition"]["y"]),
                "z": float(npc_data["spawnPosition"]["z"])
            },
            "system_prompt": str(npc_data["system_prompt"]),
            "abilities": list(npc_data.get("abilities", [])),
            "shortTermMemory": []
        }
        
        # Load existing NPCs
        npc_database = load_json_database(DB_PATHS['npc']['json'])
        if "npcs" not in npc_database:
            npc_database["npcs"] = []
            
        # Add the NPC to the database
        npc_database["npcs"].append(normalized_npc)
        
        # Save the updated database
        save_json_database(DB_PATHS['npc']['json'], npc_database)
        save_lua_database(DB_PATHS['npc']['lua'], npc_database)
        
        logger.info(f"Successfully created NPC with ID: {normalized_npc['id']}")
        return JSONResponse(normalized_npc)
        
    except Exception as e:
        logger.error(f"Error creating NPC: {e}")
        raise HTTPException(status_code=500, detail=str(e))



