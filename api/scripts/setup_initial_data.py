import json
from pathlib import Path
from api.app.config import BASE_DIR

def setup_initial_data():
    """Create initial data directory and files"""
    
    # Define initial data directory
    initial_data_dir = BASE_DIR / "initial_data" / "game1" / "src" / "data"
    initial_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Define initial asset data
    asset_data = {
        "assets": [
            {
                "assetId": "15571098041",
                "model": "tesla_cybertruck",
                "name": "Tesla Cybertruck",
                "description": "This vehicle features a flat metal, futuristic, angular vehicle reminiscent of a cybertruck. It has a sleek, gray body with distinct sharp edges and minimalistic design. Prominent characteristics include a wide, illuminated front strip, large wheel wells, and a spacious, open cabin. The overall appearance suggests a robust, modern aesthetic.",
                "imageUrl": "https://tr.rbxcdn.com/180DAY-e30fdf43661440a435b6e64373fb3850/420/420/Model/Png/noFilter",
                "type": "vehicle",
                "tags": [
                    "futuristic",
                    "angular",
                    "modern",
                    "car",
                    "electric"
                ]
            }
        ]
    }
    
    # Define initial NPC data
    npc_data = {
        "npcs": [
            {
                "id": "oz1",
                "displayName": "Oz the First",
                "assetId": "1388902922",
                "responseRadius": 20,
                "spawnPosition": {
                    "x": 20,
                    "y": 5,
                    "z": 20
                },
                "system_prompt": "You are a wise and mysterious ancient entity. You speak with authority and have knowledge of ancient secrets.",
                "shortTermMemory": [],
                "abilities": [
                    "follow",
                    "inspect",
                    "cast_spell",
                    "teach"
                ],
                "model": "old_wizard"
            }
        ]
    }
    
    # Write initial data files
    asset_file = initial_data_dir / 'AssetDatabase.json'
    npc_file = initial_data_dir / 'NPCDatabase.json'
    
    print(f"Creating initial data files in: {initial_data_dir}")
    
    with open(asset_file, 'w') as f:
        json.dump(asset_data, f, indent=4)
        print(f"Created {asset_file}")
    
    with open(npc_file, 'w') as f:
        json.dump(npc_data, f, indent=4)
        print(f"Created {npc_file}")
    
    print("Initial data setup complete")

if __name__ == "__main__":
    setup_initial_data() 