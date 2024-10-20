
# Asset Description Update Tool

## Overview

This tool is designed to update asset descriptions and image URLs in your Roblox asset database. It interacts with an AI-powered API to generate descriptions for assets based on their images. The tool can update a JSON database and optionally sync changes to a Lua file for use in Roblox.

## Features

- Update asset descriptions using AI-generated content
- Update asset image URLs
- Support for both JSON and Lua database formats
- Options to update all assets, single assets, or only assets with empty descriptions
- Ability to overwrite existing descriptions
- Sync-only mode to update Lua file from JSON without fetching new descriptions

## Prerequisites

- Python 3.7 or higher
- Required Python packages: `requests`, `argparse`

## Installation

1. Clone this repository or download the script.
2. Install required packages:

   ```
   pip install requests argparse
   ```

## Usage

The basic structure of the command is:

```
python update_asset_descriptions.py --json-file <path_to_json> [OPTIONS]
```

### Options

- `--json-file`: (Required) Path to the JSON asset database file.
- `--lua-file`: (Optional) Path to the Lua asset database file.
- `--overwrite`: (Optional) Overwrite existing descriptions.
- `--single`: (Optional) Update a single asset by ID.
- `--only-empty`: (Optional) Only update assets with empty descriptions.
- `--sync`: (Optional) Only sync JSON to Lua without updating descriptions.

## Examples

### 1. Update All Assets

To update all asset descriptions and image URLs:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua
```

This command will:
- Update all assets in the JSON file
- Generate new descriptions and fetch image URLs for all assets
- Update the Lua file with the new data

### 2. Update Single Asset

To update the description and image URL of a single asset:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua --single 15571098041
```

This will only update the asset with ID 15571098041.

### 3. Update Only Empty Descriptions

To update only assets that have no description:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua --only-empty
```

### 4. Overwrite Existing Descriptions

To update and overwrite all existing descriptions and image URLs:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua --overwrite
```

### 5. Update JSON Only

To update the JSON file without updating the Lua file:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json
```

### 6. Sync JSON to Lua Without Updating

To synchronize the JSON data to the Lua file without fetching new descriptions:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua --sync
```

### 7. Update Empty Descriptions for a Single Asset

Combine options to update only if the description is empty for a specific asset:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua --single 2958312667 --only-empty
```

### 8. Overwrite Description for a Single Asset

To overwrite the description and image URL of a specific asset, even if it already has one:

```
python update_asset_descriptions.py --json-file assets/AssetDatabase.json --lua-file src/AssetDatabase.lua --single 13292405039 --overwrite
```

## Notes

- Always ensure your JSON file is up-to-date before running update operations.
- The `--lua-file` option is optional. If not provided, only the JSON file will be updated.
- The `--sync` option is useful when you've made changes to the JSON file manually and want to reflect those changes in the Lua file without fetching new descriptions.
- Be cautious when using the `--overwrite` option, as it will replace all existing descriptions and image URLs.

## Troubleshooting

If you encounter any issues:

1. Ensure you have the latest version of the script.
2. Check that your Python version is 3.7 or higher.
3. Verify that you have installed all required packages.
4. Make sure your JSON file is properly formatted.
5. Check your internet connection, as the script needs to communicate with an external API.

If problems persist, please open an issue in the repository with a detailed description of the error and the command you used.

## Contributing

Contributions to improve the tool are welcome. Please fork the repository and submit a pull request with your changes.

## License

[MIT License](LICENSE)
