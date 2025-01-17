import argparse
import json
from typing import Dict, Any
import logging

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sync")


def convert_spawn_positions(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any table-style spawn positions to proper format and fix field names."""
    if "npcs" in data:
        for npc in data["npcs"]:
            logger.debug(f"Processing NPC: {npc.get('displayName', 'Unknown')}")
            logger.debug(f"Current NPC fields: {list(npc.keys())}")
            
            # Fix assetID to assetId
            if "assetID" in npc:
                npc["assetId"] = npc["assetID"]
                del npc["assetID"]
            
            # Ensure model field exists and follows correct naming convention
            if "model" not in npc:
                if "displayName" not in npc:
                    logger.error(f"NPC missing both model and displayName: {npc}")
                    npc["model"] = "DefaultNPCModel"
                    npc["displayName"] = "Unknown NPC"
                else:
                    # Convert display name to proper model name format
                    # Example: "Oz the First" -> "NPCModel_OzTheFirst"
                    model_name = "NPCModel_" + "".join(
                        word.capitalize() 
                        for word in npc["displayName"].split()
                    )
                    npc["model"] = model_name
                logger.debug(f"Added model field: {npc['model']}")
            
            # Ensure spawn position is in correct format
            if "spawnPosition" in npc:
                pos = npc["spawnPosition"]
                if isinstance(pos, dict) and all(k in pos for k in ["x", "y", "z"]):
                    continue
                elif isinstance(pos, str):
                    try:
                        x, y, z = map(float, pos.split(","))
                        npc["spawnPosition"] = {"x": x, "y": y, "z": z}
                    except:
                        npc["spawnPosition"] = {"x": 0, "y": 5, "z": 0}
                else:
                    npc["spawnPosition"] = {"x": 0, "y": 5, "z": 0}
            else:
                npc["spawnPosition"] = {"x": 0, "y": 5, "z": 0} 

            # Ensure other required fields with logging
            required_fields = {
                "responseRadius": 25,
                "shortTermMemory": [],
                "abilities": ["follow", "inspect"],
                "system_prompt": "I am an NPC."  # Adding default system prompt
            }
            
            for field, default_value in required_fields.items():
                if field not in npc:
                    npc[field] = default_value
                    logger.debug(f"Added missing field {field} with default value")

    return data


def save_lua_database(path: str, data: Dict[str, Any]) -> None:
    """Save data to a Lua database file with proper Roblox formatting."""
    try:
        with open(path, 'w') as f:
            f.write("return {\n")
            
            # Handle assets table
            if "assets" in data:
                f.write("    assets = {\n")
                for asset in data["assets"]:
                    f.write("        {\n")
                    f.write(f'            assetId = "{asset["assetId"]}",\n')
                    f.write(f'            name = "{asset["name"]}",\n')
                    # Escape any quotes in the description
                    description = asset["description"].replace('"', '\\"')
                    f.write(f'            description = "{description}",\n')
                    f.write(f'            imageUrl = "{asset["imageUrl"]}",\n')
                    f.write("        },\n")
                f.write("    },\n")
            
            # Handle NPCs table with proper Roblox formatting
            if "npcs" in data:
                f.write("    npcs = {\n")
                for npc in data["npcs"]:
                    f.write("        {\n")
                    # Required fields
                    f.write(f'            id = "{npc["id"]}",\n')
                    f.write(f'            displayName = "{npc["displayName"]}",\n')
                    f.write(f'            model = "{npc["model"]}",\n')
                    f.write(f'            responseRadius = {npc["responseRadius"]},\n')
                    
                    # Convert spawn position to Vector3
                    spawn_pos = npc["spawnPosition"]
                    f.write(f'            spawnPosition = Vector3.new({spawn_pos["x"]}, {spawn_pos["y"]}, {spawn_pos["z"]}),\n')
                    
                    # System prompt with escaped quotes
                    system_prompt = npc["system_prompt"].replace('"', '\\"')
                    f.write(f'            system_prompt = "{system_prompt}",\n')
                    
                    # Optional fields with defaults
                    f.write(f'            shortTermMemory = {{}},\n')
                    f.write(f'            assetId = "{npc.get("assetId", "")}", -- For asset linking\n')
                    
                    # Handle abilities array
                    if "abilities" in npc and npc["abilities"]:
                        f.write('            abilities = {\n')
                        for ability in npc["abilities"]:
                            f.write(f'                "{ability}",\n')
                        f.write('            },\n')
                    else:
                        f.write('            abilities = {},\n')
                    
                    f.write("        },\n")
                f.write("    },\n")
            
            # Handle players table
            if "players" in data:
                f.write("    players = {\n")
                for player in data["players"]:
                    f.write("        {\n")
                    f.write(f'            playerID = "{player["playerID"]}",\n')
                    f.write(f'            displayName = "{player["displayName"]}",\n')
                    if "description" in player:
                        description = player["description"].replace('"', '\\"')
                        f.write(f'            description = "{description}",\n')
                    f.write("        },\n")
                f.write("    },\n")
            
            f.write("}\n")
            
        logger.info(f"Successfully saved Lua database to {path}")
    except Exception as e:
        logger.error(f"Error saving Lua database to {path}: {e}")
        raise


def sync_asset_database(json_path: str, lua_path: str, backup: bool = False) -> None:
    """Sync the asset database specifically."""
    logger.info(f"Syncing asset database from {json_path} to {lua_path}")
    
    try:
        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Create backup if requested
        if backup:
            backup_path = json_path + '.backup'
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Created backup at {backup_path}")
        
        # Ensure assets exist
        if "assets" not in data:
            data["assets"] = []
        
        # Validate asset data
        for asset in data["assets"]:
            required_fields = ["assetId", "name", "description", "imageUrl"]
            for field in required_fields:
                if field not in asset:
                    logger.warning(f"Asset missing required field {field}: {asset}")
                    if field == "description":
                        asset[field] = ""
                    elif field == "imageUrl":
                        asset[field] = ""
                    elif field == "name":
                        asset[field] = f"Asset_{asset.get('assetId', 'unknown')}"
        
        # Save to Lua
        save_lua_database(lua_path, data)
        logger.info("Asset database sync completed successfully")
        
    except Exception as e:
        logger.error(f"Error syncing asset database: {e}")
        raise


def sync_databases():
    parser = argparse.ArgumentParser(description="Sync and fix database formats")
    parser.add_argument("--json-file", required=True, help="Path to JSON database")
    parser.add_argument("--lua-file", required=True, help="Path to Lua database")
    parser.add_argument("--backup", action="store_true", help="Create backup of original files")
    parser.add_argument("--type", choices=["npc", "asset", "player"], 
                      help="Type of database to sync")
    
    args = parser.parse_args()
    
    if args.type == "asset":
        sync_asset_database(args.json_file, args.lua_file, args.backup)
    else:
        # Existing NPC/player sync code...
        with open(args.json_file, 'r') as f:
            data = json.load(f)
        
        fixed_data = convert_spawn_positions(data)
        
        if args.backup:
            with open(args.json_file + '.backup', 'w') as f:
                json.dump(data, f, indent=2)
                
        with open(args.json_file, 'w') as f:
            json.dump(fixed_data, f, indent=2)
            
        save_lua_database(args.lua_file, fixed_data)
    
    print("Database sync completed successfully!")


if __name__ == "__main__":
    sync_databases()
