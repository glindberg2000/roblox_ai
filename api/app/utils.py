import os
import logging
import json
from typing import Any, Dict

logger = logging.getLogger("roblox_app")

def load_json_database(path: str) -> Dict[str, Any]:
    """Load a JSON database file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON database from {path}: {e}")
        raise

def save_json_database(path: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON database file."""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving JSON database to {path}: {e}")
        raise

def _value_to_lua(value: Any, indent_level: int = 0) -> str:
    """Convert a Python value to its Lua representation."""
    indent = "    " * indent_level
    
    if isinstance(value, str):
        # Escape quotes and newlines in strings
        escaped = value.replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        if not value:  # Empty list
            return "{}"
        items = [_value_to_lua(item, indent_level + 1) for item in value]
        return "{\n" + indent + "    " + ",\n    ".join(items) + "\n" + indent + "}"
    elif isinstance(value, dict):
        if not value:  # Empty dict
            return "{}"
        items = []
        for k, v in value.items():
            lua_value = _value_to_lua(v, indent_level + 1)
            items.append(f"{k} = {lua_value}")
        return "{\n" + indent + "    " + ",\n    ".join(items) + "\n" + indent + "}"
    elif value is None:
        return "nil"
    else:
        raise ValueError(f"Unsupported type for Lua conversion: {type(value)}")

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
                    for key, value in asset.items():
                        # Handle different value types
                        if isinstance(value, str):
                            # Escape quotes in strings
                            escaped_value = value.replace('"', '\\"')
                            f.write(f'            {key} = "{escaped_value}",\n')
                        elif isinstance(value, (int, float)):
                            f.write(f'            {key} = {value},\n')
                        elif isinstance(value, bool):
                            f.write(f'            {key} = {str(value).lower()},\n')
                        elif isinstance(value, list):
                            # Fixed the problematic f-string
                            items = ", ".join(f'"{x}"' for x in value)
                            f.write(f'            {key} = {{ {items} }},\n')
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
                    f.write(f'            assetId = "{npc["assetId"]}",\n')  # Changed from assetID
                    f.write(f'            model = "{npc["model"]}",\n')
                    f.write(f'            responseRadius = {npc["responseRadius"]},\n')
                    
                    # Convert spawn position to Vector3
                    spawn_pos = npc["spawnPosition"]
                    f.write(f'            spawnPosition = Vector3.new({spawn_pos["x"]}, {spawn_pos["y"]}, {spawn_pos["z"]}),\n')
                    
                    # System prompt with escaped quotes
                    system_prompt = npc["system_prompt"].replace('"', '\\"')
                    f.write(f'            system_prompt = "{system_prompt}",\n')
                    
                    # Empty table for shortTermMemory
                    f.write('            shortTermMemory = {},\n')
                    
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
                    # Required fields
                    f.write(f'            id = "{player["id"]}",\n')
                    f.write(f'            displayName = "{player["displayName"]}",\n')
                    f.write(f'            assetId = "{player["assetId"]}",\n')  # Changed from assetID
                    f.write(f'            model = "{player["model"]}",\n')
                    f.write(f'            responseRadius = {player["responseRadius"]},\n')
                    
                    # Convert spawn position to Vector3
                    spawn_pos = player["spawnPosition"]
                    f.write(f'            spawnPosition = Vector3.new({spawn_pos["x"]}, {spawn_pos["y"]}, {spawn_pos["z"]}),\n')
                    
                    # System prompt with escaped quotes
                    system_prompt = player["system_prompt"].replace('"', '\\"')
                    f.write(f'            system_prompt = "{system_prompt}",\n')
                    
                    # Empty table for shortTermMemory
                    f.write('            shortTermMemory = {},\n')
                    
                    # Handle abilities array
                    if "abilities" in player and player["abilities"]:
                        f.write('            abilities = {\n')
                        for ability in player["abilities"]:
                            f.write(f'                "{ability}",\n')
                        f.write('            },\n')
                    else:
                        f.write('            abilities = {},\n')
                    
                    f.write("        },\n")
                f.write("    },\n")
            
            f.write("}\n")
            
        logger.info(f"Successfully saved Lua database to {path}")
    except Exception as e:
        logger.error(f"Error saving Lua database to {path}: {e}")
        raise
    
def get_database_paths():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'data'))
    return {
        'asset': {
            'json': os.path.join(base_path, 'AssetDatabase.json'),
            'lua': os.path.join(base_path, 'AssetDatabase.lua')
        },
        'npc': {
            'json': os.path.join(base_path, 'NPCDatabase.json'),
            'lua': os.path.join(base_path, 'NPCDatabase.lua')
        },
        'player': {
            'json': os.path.join(base_path, 'PlayerDatabase.json'),
            'lua': os.path.join(base_path, 'PlayerDatabase.lua')
        }
    }
