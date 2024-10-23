import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from .utils import load_json_database, save_json_database, save_lua_database, get_database_paths

# Initialize logging
logger = logging.getLogger("ella_app")
router = APIRouter()

# Get database paths
DB_PATHS = get_database_paths()

# Pydantic Models for Dashboard
class AssetData(BaseModel):
    asset_id: str
    name: str

class EditItemRequest(BaseModel):
    description: str

class UpdateAssetsRequest(BaseModel):
    overwrite: bool = False
    single_asset: Optional[str] = None
    only_empty: bool = False

# Asset Routes
@router.get("/assets")  # Now accessible at /assets
async def get_assets():
    try:
        asset_data = load_json_database(DB_PATHS['asset']['json'])
        assets = [
            {
                "id": asset["assetId"],
                "name": asset["name"],
                "description": asset["description"],
                "image_url": asset["imageUrl"]
            }
            for asset in asset_data["assets"]
        ]
        return JSONResponse({"assets": assets})
    except Exception as e:
        logger.error(f"Error fetching asset data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch asset data")

@router.post("/add_asset")  # Now accessible at /add_asset
async def add_asset(asset: AssetData):
    try:
        # Note: We'll need to implement asset description generation here
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        new_asset = {
            "assetId": asset.asset_id,
            "name": asset.name,
            "description": f"Description for {asset.name}",  # Placeholder
            "imageUrl": ""  # Placeholder
        }
        asset_database["assets"].append(new_asset)
        save_json_database(DB_PATHS['asset']['json'], asset_database)
        save_lua_database(DB_PATHS['asset']['lua'], asset_database)
        return JSONResponse(new_asset)
    except Exception as e:
        logger.error(f"Error adding new asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to add new asset")

@router.delete("/delete_asset/{asset_id}")  # Now accessible at /delete_asset/{asset_id}
async def delete_asset(asset_id: str):
    try:
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        original_length = len(asset_database["assets"])
        asset_database["assets"] = [a for a in asset_database["assets"] if a["assetId"] != asset_id]
        if len(asset_database["assets"]) == original_length:
            raise HTTPException(status_code=404, detail="Asset not found")
        save_json_database(DB_PATHS['asset']['json'], asset_database)
        save_lua_database(DB_PATHS['asset']['lua'], asset_database)
        return JSONResponse({"message": f"Asset {asset_id} deleted successfully"})
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete asset")

@router.put("/edit_asset/{asset_id}")  # Now accessible at /edit_asset/{asset_id}
async def edit_asset(asset_id: str, request: EditItemRequest):
    try:
        asset_database = load_json_database(DB_PATHS['asset']['json'])
        for asset in asset_database["assets"]:
            if asset["assetId"] == asset_id:
                asset["description"] = request.description
                save_json_database(DB_PATHS['asset']['json'], asset_database)
                save_lua_database(DB_PATHS['asset']['lua'], asset_database)
                return JSONResponse({"message": "Asset updated successfully"})
        raise HTTPException(status_code=404, detail="Asset not found")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to update asset")

# NPC Routes
@router.get("/api/npcs")  # Now accessible at /api/npcs
async def get_npcs():
    try:
        npc_data = load_json_database(DB_PATHS['npc']['json'])
        return JSONResponse({"npcs": npc_data["npcs"]})
    except Exception as e:
        logger.error(f"Error fetching NPC data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NPC data")

# Player Routes
@router.get("/api/players")  # Now accessible at /api/players
async def get_players():
    try:
        player_data = load_json_database(DB_PATHS['player']['json'])
        return JSONResponse({"players": player_data["players"]})
    except Exception as e:
        logger.error(f"Error fetching player data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch player data")
