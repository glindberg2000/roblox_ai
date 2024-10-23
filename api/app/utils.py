import os
import logging
import json
from typing import Any, Dict

logger = logging.getLogger("ella_app")

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

def save_lua_database(path: str, data: Dict[str, Any]) -> None:
    """Save data to a Lua database file."""
    try:
        with open(path, 'w') as f:
            f.write("return {\n")
            # Convert the JSON structure to Lua
            if "assets" in data:
                f.write("    assets = {\n")
                for asset in data["assets"]:
                    f.write("        {\n")
                    for key, value in asset.items():
                        if isinstance(value, str):
                            f.write(f'            {key} = "{value}",\n')
                        else:
                            f.write(f"            {key} = {value},\n")
                    f.write("        },\n")
                f.write("    },\n")
            f.write("}\n")
    except Exception as e:
        logger.error(f"Error saving Lua database to {path}: {e}")
        raise

# Database file paths
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
