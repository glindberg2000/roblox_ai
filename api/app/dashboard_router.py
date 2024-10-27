import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import xml.etree.ElementTree as ET
from .utils import load_json_database, save_json_database, save_lua_database, get_database_paths
from .storage import FileStorageManager
from .image_utils import get_asset_description
from .config import STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR

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
async def create_asset(data: str = Form(...), file: Optional[UploadFile] = None):
    try:
        logger.info("Processing asset creation request")
        asset_data = json.loads(data)
        
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
            file_info = await file_manager.store_asset_file(file, asset_data["assetId"])

        # Create asset entry
        new_asset = {
            "assetId": asset_data["assetId"],
            "name": asset_data["name"],
            "description": description_response["description"],
            "imageUrl": description_response["imageUrl"]
        }

        if file_info:
            new_asset["sourceFile"] = file_info

        # Update database
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        asset_database["assets"].append(new_asset)
        save_json_database(DB_PATHS['asset']['json'], asset_database)
        save_lua_database(DB_PATHS['asset']['lua'], asset_database)
        
        return JSONResponse(new_asset)

    except Exception as e:
        logger.error(f"Error creating asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create asset: {str(e)}")

@router.get("/api/assets")
async def get_assets():
    try:
        asset_data = load_json_database(DB_PATHS['asset']['json'])
        return JSONResponse({"assets": asset_data["assets"]})
    except Exception as e:
        logger.error(f"Error fetching asset data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch asset data")

@router.put("/api/assets/{asset_id}")
async def update_asset(asset_id: str, item: EditItemRequest):
    try:
        logger.info(f"Attempting to update asset {asset_id}")
        if not asset_id:
            raise HTTPException(status_code=400, detail="Asset ID is required")
            
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        
        asset_found = False
        for asset in asset_database["assets"]:
            if asset["assetId"] == asset_id:
                asset_found = True
                asset["name"] = item.name
                asset["description"] = item.description
                save_json_database(DB_PATHS['asset']['json'], asset_database)
                save_lua_database(DB_PATHS['asset']['lua'], asset_database)
                logger.info(f"Successfully updated asset {asset_id}")
                return JSONResponse(asset)
                
        if not asset_found:
            raise HTTPException(status_code=404, detail="Asset not found")
            
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
    try:
        npc_data = load_json_database(DB_PATHS['npc']['json'])
        # Transform the data to use system_prompt for display
        for npc in npc_data["npcs"]:
            if "description" in npc:
                del npc["description"]  # Remove description field if it exists
        return JSONResponse({"npcs": npc_data["npcs"]})
    except Exception as e:
        logger.error(f"Error fetching NPC data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NPC data")

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
                # Update the system_prompt if it's being edited
                if "description" in npc_data:
                    npc["system_prompt"] = npc_data["description"]
                    if "description" in npc:
                        del npc["description"]
                
                # Update other fields
                for key, value in npc_data.items():
                    if key != "description":  # Skip description field
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
    




