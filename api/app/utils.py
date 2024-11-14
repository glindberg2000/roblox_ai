import json
from pathlib import Path

def get_database_paths(game_slug="game1"):
    """Get paths to database files"""
    root_dir = Path(__file__).parent.parent.parent
    game_dir = root_dir / "games" / game_slug / "src"
    
    return {
        'asset': {
            'json': game_dir / 'data' / 'AssetDatabase.json',
            'lua': game_dir / 'data' / 'AssetDatabase.lua'
        },
        'npc': {
            'json': game_dir / 'data' / 'NPCDatabase.json',
            'lua': game_dir / 'data' / 'NPCDatabase.lua'
        }
    }

def load_json_database(path):
    """Load a JSON database file"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON database from {path}: {e}")
        return {"assets": []}

def save_json_database(path, data):
    """Save data to a JSON database file"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving JSON database to {path}: {e}")
        raise

def save_lua_database(path, data):
    """Save data as a Lua table"""
    try:
        with open(path, 'w') as f:
            f.write("return {\n")
            
            # Write assets if present
            if "assets" in data:
                f.write("    assets = {\n")
                for asset in data.get("assets", []):
                    f.write("        {\n")
                    f.write(f'            assetId = "{asset["assetId"]}",\n')
                    f.write(f'            name = "{asset["name"]}",\n')
                    f.write(f'            description = "{asset.get("description", "")}",\n')
                    f.write("        },\n")
                f.write("    },\n")
            
            # Write NPCs if present
            if "npcs" in data:
                f.write("    npcs = {\n")
                for npc in data.get("npcs", []):
                    f.write("        {\n")
                    f.write(f'            id = "{npc.get("id", "")}",\n')
                    f.write(f'            displayName = "{npc.get("displayName", "Unknown NPC")}",\n')
                    f.write(f'            model = "{npc.get("model", "")}",\n')
                    f.write(f'            responseRadius = {npc.get("responseRadius", 20)},\n')
                    f.write(f'            assetId = "{npc["assetId"]}",\n')
                    
                    # Handle spawnPosition using Vector3.new()
                    spawn = npc.get("spawnPosition", {})
                    f.write(f'            spawnPosition = Vector3.new({spawn.get("x", 0)}, {spawn.get("y", 0)}, {spawn.get("z", 0)}),\n')
                    
                    # Handle system prompt with [[ ]] for multi-line strings
                    f.write(f'            system_prompt = [[{npc.get("system_prompt", "")}]],\n')
                    
                    # Handle abilities
                    f.write('            abilities = {\n')
                    for ability in npc.get("abilities", []):
                        f.write(f'                "{ability}",\n')
                    f.write('            },\n')
                    
                    # Add shortTermMemory
                    f.write('            shortTermMemory = {},\n')
                    
                    f.write("        },\n")
                f.write("    },\n")
            
            f.write("}\n")
    except Exception as e:
        print(f"Error saving Lua database to {path}: {e}")
        raise
