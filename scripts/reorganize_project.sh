#!/bin/bash

# Exit on any error
set -e

echo "Starting project reorganization..."

# Get the project root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$ROOT_DIR"

# Create new directory structure
echo "Creating new directory structure..."
mkdir -p games/game1/src/{data,assets/npcs,game_specific/{server,client}}
mkdir -p shared/{modules,utils}

# Move (not copy) data files to game1
echo "Moving data files to game1..."
mv src/data/*.{json,lua} games/game1/src/data/

# Move game-specific server scripts
echo "Moving server scripts..."
mv src/server/*.lua games/game1/src/game_specific/server/

# Move game-specific client scripts
echo "Moving client scripts..."
mv src/client/*.lua games/game1/src/game_specific/client/

# Move shared code
echo "Moving shared code..."
mv src/shared/*.lua shared/modules/

# Move assets
echo "Moving assets..."
mv src/assets/* games/game1/src/assets/

# Remove any existing symlinks
echo "Removing old symlinks..."
rm -f games/game1/shared

# Copy Rojo project file
echo "Setting up Rojo configuration..."
cat > games/game1/default.project.json << 'EOL'
{
  "name": "Game1",
  "tree": {
    "$className": "DataModel",
    "ServerStorage": {
      "$className": "ServerStorage",
      "Assets": {
        "$className": "Folder",
        "npcs": {
          "$path": "src/assets/npcs"
        }
      }
    },
    "ReplicatedStorage": {
      "$className": "ReplicatedStorage",
      "Shared": {
        "$className": "Folder",
        "NPCManagerV3": {
          "$path": "../../shared/modules/NPCManagerV3.lua"
        },
        "AssetModule": {
          "$path": "../../shared/modules/AssetModule.lua"
        }
      },
      "GameData": {
        "$path": "src/data"
      }
    },
    "ServerScriptService": {
      "$className": "ServerScriptService",
      "GameScripts": {
        "$path": "src/game_specific/server"
      }
    },
    "StarterPlayer": {
      "$className": "StarterPlayer",
      "StarterPlayerScripts": {
        "$className": "StarterPlayerScripts",
        "GameScripts": {
          "$path": "src/game_specific/client"
        }
      }
    }
  }
}
EOL

# Create backup of old structure
echo "Creating backup of old structure..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
tar -czf backups/src_backup_${timestamp}.tar.gz src/

# Remove empty src directories
echo "Cleaning up empty directories..."
rm -rf src/data src/server src/client src/shared src/assets
[ -d src ] && rmdir --ignore-fail-on-non-empty src/

echo "Reorganization complete!"
echo "Old structure backed up to: backups/src_backup_${timestamp}.tar.gz"
echo ""
echo "New structure:"
echo "  games/game1/          - Game-specific code and data"
echo "    ├── src/           "
echo "    │   ├── data/      - Game data files"
echo "    │   ├── assets/    - Game assets"
echo "    │   └── game_specific/"
echo "    │       ├── server/ - Server scripts"
echo "    │       └── client/ - Client scripts"
echo "    └── default.project.json"
echo ""
echo "  shared/              - Shared code between games"
echo "    ├── modules/       - Shared modules"
echo "    └── utils/         - Shared utilities"
echo ""
echo "Next steps:"
echo "1. Test game1 with 'rojo serve' in games/game1 directory"
echo "2. Update paths in your code if necessary"
echo "3. Create additional game directories as needed" 