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

def save_lua_database(filepath: str, data: Dict) -> None:
    """Save database as a Lua module."""
    try:
        # Start with the module header
        lua_content = "return {\n"
        
        # For NPCs database
        if "npcs" in data:
            lua_content += "    npcs = {\n"
            for npc in data["npcs"]:
                lua_content += "        {\n"
                lua_content += f'            id = "{npc.get("id", "")}", \n'
                lua_content += f'            displayName = "{npc.get("displayName", "")}", \n'
                lua_content += f'            model = "{npc.get("model", "")}", \n'
                lua_content += f'            responseRadius = {npc.get("responseRadius", 0)}, \n'
                lua_content += f'            assetId = "{npc.get("assetId", "")}", \n'
                
                # Generate Vector3 for spawn position
                spawn_pos = npc.get("spawnPosition", {"x": 0, "y": 5, "z": 0})
                lua_content += f'            spawnPosition = Vector3.new({spawn_pos.get("x", 0)}, {spawn_pos.get("y", 5)}, {spawn_pos.get("z", 0)}),\n'
                
                lua_content += f'            system_prompt = "{npc.get("system_prompt", "")}", \n'
                
                # Add abilities array
                abilities = npc.get("abilities", [])
                lua_content += '            abilities = {\n'
                for ability in abilities:
                    lua_content += f'                "{ability}",\n'
                lua_content += '            },\n'
                
                lua_content += '            shortTermMemory = {},\n'
                lua_content += "        },\n"
            lua_content += "    },\n"
            
        # For assets database
        elif "assets" in data:
            lua_content += "    assets = {\n"
            for asset in data["assets"]:
                lua_content += "        {\n"
                lua_content += f'            assetId = "{asset.get("assetId", "")}", \n'
                lua_content += f'            name = "{asset.get("name", "")}", \n'
                lua_content += f'            description = "{asset.get("description", "")}", \n'
                lua_content += "        },\n"
            lua_content += "    },\n"
            
        # Close the module
        lua_content += "}\n"
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(lua_content)
            
    except Exception as e:
        logger.error(f"Error saving Lua database to {filepath}: {str(e)}")
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
