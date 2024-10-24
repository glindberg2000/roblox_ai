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
    """Convert any table-style spawn positions to proper format."""
    if "npcs" in data:
        for npc in data["npcs"]:
            # Ensure spawn position is in correct format
            if "spawnPosition" in npc:
                pos = npc["spawnPosition"]
                if isinstance(pos, dict) and all(k in pos for k in ["x", "y", "z"]):
                    continue  # Already in correct format
                elif isinstance(pos, str):
                    # Handle potential string format like "0, 5, 0"
                    try:
                        x, y, z = map(float, pos.split(","))
                        npc["spawnPosition"] = {"x": x, "y": y, "z": z}
                    except:
                        npc["spawnPosition"] = {"x": 0, "y": 5, "z": 0}  # Default
                else:
                    # Set default spawn position if invalid
                    npc["spawnPosition"] = {"x": 0, "y": 5, "z": 0}
            else:
                # Add spawn position if missing
                npc["spawnPosition"] = {"x": 0, "y": 5, "z": 0}

            # Ensure other required fields
            if "model" not in npc:
                npc["model"] = npc["displayName"].replace(" ", "")
            if "responseRadius" not in npc:
                npc["responseRadius"] = 25
            if "shortTermMemory" not in npc:
                npc["shortTermMemory"] = []

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
                    f.write(f'            assetID = "{npc.get("assetID", "")}", -- For asset linking\n')
                    
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

def sync_databases():
    parser = argparse.ArgumentParser(description="Sync and fix database formats")
    parser.add_argument("--json-file", required=True, help="Path to JSON database")
    parser.add_argument("--lua-file", required=True, help="Path to Lua database")
    parser.add_argument("--backup", action="store_true", help="Create backup of original files")
    
    args = parser.parse_args()

    # Load and convert JSON data
    with open(args.json_file, 'r') as f:
        data = json.load(f)
    
    # Fix data format
    fixed_data = convert_spawn_positions(data)
    
    # Save back to JSON
    if args.backup:
        with open(args.json_file + '.backup', 'w') as f:
            json.dump(data, f, indent=2)
            
    with open(args.json_file, 'w') as f:
        json.dump(fixed_data, f, indent=2)
        
    # Save to Lua
    save_lua_database(args.lua_file, fixed_data)
    
    print("Database sync completed successfully!")

if __name__ == "__main__":
    sync_databases()