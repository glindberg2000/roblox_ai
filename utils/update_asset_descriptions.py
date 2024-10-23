#update_asset_descriptions.py

import json
import argparse
import requests
from typing import Dict

API_URL = "http://localhost:8000/get_asset_description"  # Update this URL if your API is hosted elsewhere

def load_json_database(file_path: str) -> Dict:
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_database(file_path: str, data: Dict):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def save_lua_database(file_path: str, data: Dict):
    def escape_lua_string(s):
        # Replace newlines with \n and escape any existing backslashes
        s = s.replace('\\', '\\\\').replace('\n', '\\n')
        # Replace double quotes with single quotes
        s = s.replace('"', "'")
        return s

    content = "return {\n  assets = {\n"
    for asset in data['assets']:
        content += "    {\n"
        for key, value in asset.items():
            if key == 'assetId':
                content += f'      assetId = "{value}", -- {asset["name"]}\n'
            elif key == 'description':
                # Use [[ ]] for description to avoid issues with quotes and special characters
                escaped_value = escape_lua_string(value)
                content += f'      {key} = [[{escaped_value}]],\n'
            else:
                escaped_value = escape_lua_string(value)
                content += f'      {key} = "{escaped_value}",\n'
        content += "    },\n"
    content += "  }\n}"
    
    with open(file_path, 'w') as f:
        f.write(content)

def get_asset_description(asset_id: str, asset_name: str) -> Dict[str, str]:
    try:
        response = requests.post(API_URL, json={"asset_id": asset_id, "name": asset_name})
        response.raise_for_status()
        data = response.json()
        return {
            "description": data.get("description", ""),
            "imageUrl": data.get("imageUrl", "")
        }
    except requests.RequestException as e:
        print(f"Error getting description for asset {asset_id}: {str(e)}")
        return {"description": "", "imageUrl": ""}

def update_asset_descriptions(
    asset_db: Dict,
    overwrite: bool = False,
    single_asset: str = None,
    only_empty: bool = False
) -> Dict:
    updated_assets = []
    
    assets_to_update = asset_db['assets']
    if single_asset:
        assets_to_update = [asset for asset in assets_to_update if asset['assetId'] == single_asset]

    for asset in assets_to_update:
        if only_empty and asset.get('description'):
            continue
        if not overwrite and asset.get('description'):
            continue
        
        new_data = get_asset_description(asset['assetId'], asset['name'])
        if new_data["description"]:
            asset['description'] = new_data["description"]
            asset['imageUrl'] = new_data["imageUrl"]
            updated_assets.append(asset['assetId'])

    print(f"Updated descriptions for {len(updated_assets)} assets: {', '.join(updated_assets)}")
    return asset_db

def main():
    parser = argparse.ArgumentParser(description="Update asset descriptions in AssetDatabase")
    parser.add_argument("--json-file", required=True, help="Path to AssetDatabase.json file")
    parser.add_argument("--lua-file", help="Path to AssetDatabase.lua file")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing descriptions")
    parser.add_argument("--single", help="Update a single asset by ID")
    parser.add_argument("--only-empty", action="store_true", help="Only update empty descriptions")
    parser.add_argument("--sync", action="store_true", help="Only sync JSON to Lua without updating descriptions")
    
    args = parser.parse_args()

    # Load data from JSON file
    asset_db = load_json_database(args.json_file)
    
    if not args.sync:
        # Update descriptions
        updated_db = update_asset_descriptions(
            asset_db,
            overwrite=args.overwrite,
            single_asset=args.single,
            only_empty=args.only_empty
        )
        
        # Save updated data to JSON file
        save_json_database(args.json_file, updated_db)
        print(f"AssetDatabase updated and saved to {args.json_file}")
    else:
        print("Syncing JSON to Lua without updating descriptions")

    # If Lua file path is provided, save to Lua file
    if args.lua_file:
        save_lua_database(args.lua_file, asset_db)
        print(f"AssetDatabase saved to Lua file: {args.lua_file}")

if __name__ == "__main__":
    main()
