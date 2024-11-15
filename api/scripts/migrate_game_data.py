import json
from pathlib import Path
from api.app.config import BASE_DIR, get_game_paths
from api.app.utils import get_database_paths, save_lua_database

def migrate_game_data():
    """Generate Lua files from existing JSON data"""
    
    # Get paths for game1
    game_paths = get_game_paths("game1")
    db_paths = get_database_paths("game1")
    
    print("Starting Lua file generation...")
    
    try:
        # Define paths
        initial_data_dir = BASE_DIR / "initial_data" / "game1" / "src" / "data"
        game_data_dir = game_paths['data']
        
        print(f"Checking initial data in: {initial_data_dir}")
        print(f"Checking game data in: {game_data_dir}")
        
        # Load JSON data (try game directory first, then initial data)
        asset_data = {"assets": []}
        npc_data = {"npcs": []}
        
        # Try loading from game directory first
        try:
            if (game_data_dir / 'AssetDatabase.json').exists():
                with open(game_data_dir / 'AssetDatabase.json', 'r') as f:
                    asset_data = json.load(f)
                    print(f"Loaded {len(asset_data.get('assets', []))} assets from game directory")
            
            if (game_data_dir / 'NPCDatabase.json').exists():
                with open(game_data_dir / 'NPCDatabase.json', 'r') as f:
                    npc_data = json.load(f)
                    print(f"Loaded {len(npc_data.get('npcs', []))} NPCs from game directory")
        except Exception as e:
            print(f"Error loading from game directory: {e}")
        
        # If no data found, try initial data
        if not asset_data.get('assets') and not npc_data.get('npcs'):
            try:
                if (initial_data_dir / 'AssetDatabase.json').exists():
                    with open(initial_data_dir / 'AssetDatabase.json', 'r') as f:
                        asset_data = json.load(f)
                        print(f"Loaded {len(asset_data.get('assets', []))} assets from initial data")
                
                if (initial_data_dir / 'NPCDatabase.json').exists():
                    with open(initial_data_dir / 'NPCDatabase.json', 'r') as f:
                        npc_data = json.load(f)
                        print(f"Loaded {len(npc_data.get('npcs', []))} NPCs from initial data")
            except Exception as e:
                print(f"Error loading from initial data: {e}")
        
        if not asset_data.get('assets') and not npc_data.get('npcs'):
            print("No data found in either location!")
            return
        
        # Generate Lua files
        print("\nGenerating Lua files:")
        
        # Assets Lua file
        if asset_data.get('assets'):
            save_lua_database(db_paths['asset']['lua'], {"assets": asset_data['assets']})
            print(f"Created asset Lua file at: {db_paths['asset']['lua']}")
            print(f"With {len(asset_data['assets'])} assets")
        
        # NPCs Lua file
        if npc_data.get('npcs'):
            save_lua_database(db_paths['npc']['lua'], {"npcs": npc_data['npcs']})
            print(f"Created NPC Lua file at: {db_paths['npc']['lua']}")
            print(f"With {len(npc_data['npcs'])} NPCs")
        
        print("\nLua file generation complete")
            
    except Exception as e:
        print(f"Error during Lua file generation: {e}")
        raise

if __name__ == "__main__":
    migrate_game_data() 