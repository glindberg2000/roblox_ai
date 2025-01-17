#!/bin/bash

# Exit on any error
set -e

echo "Starting structure update..."

# Get the project root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$ROOT_DIR"

# Function to create game structure
create_game_structure() {
    local game_name=$1
    echo "Creating structure for $game_name..."
    
    mkdir -p games/$game_name/src/{data,assets,server,client,shared}
    
    # Copy project.json template
    cat > games/$game_name/default.project.json << 'EOL'
{
  "name": "Game1",
  "tree": {
    "$className": "DataModel",
    "ReplicatedStorage": {
      "$className": "ReplicatedStorage",
      "GlobalShared": {
        "$className": "Folder",
        "NPCManagerV3": {
          "$path": "../../shared/modules/NPCManagerV3.lua"
        },
        "AssetModule": {
          "$path": "../../shared/modules/AssetModule.lua"
        }
      },
      "Shared": {
        "$path": "src/shared"
      },
      "GameData": {
        "$path": "src/data"
      }
    },
    "ServerStorage": {
      "$className": "ServerStorage",
      "Assets": {
        "$path": "src/assets"
      }
    },
    "ServerScriptService": {
      "$className": "ServerScriptService",
      "Server": {
        "$path": "src/server"
      }
    },
    "StarterPlayer": {
      "$className": "StarterPlayer",
      "StarterPlayerScripts": {
        "$className": "StarterPlayerScripts",
        "Client": {
          "$path": "src/client"
        }
      }
    }
  }
}
EOL
}

# Create shared modules structure
echo "Creating shared modules structure..."
mkdir -p shared/modules

# Move shared code to shared/modules
if [ -f "src/shared/NPCManagerV3.lua" ]; then
    mv src/shared/NPCManagerV3.lua shared/modules/
fi
if [ -f "src/shared/AssetModule.lua" ]; then
    mv src/shared/AssetModule.lua shared/modules/
fi

# Create game1 structure
create_game_structure "game1"

# Move game-specific files
echo "Moving game-specific files..."
if [ -d "src/data" ]; then
    mv src/data/* games/game1/src/data/ 2>/dev/null || true
fi
if [ -d "src/assets" ]; then
    mv src/assets/* games/game1/src/assets/ 2>/dev/null || true
fi
if [ -d "src/server" ]; then
    mv src/server/* games/game1/src/server/ 2>/dev/null || true
fi
if [ -d "src/client" ]; then
    mv src/client/* games/game1/src/client/ 2>/dev/null || true
fi

# Remove old directories
echo "Cleaning up old directories..."
rm -rf src/data src/assets src/server src/client src/shared
[ -d src ] && rmdir --ignore-fail-on-non-empty src/

# Remove any existing symlinks
echo "Removing symlinks..."
find . -type l ! -path "./roblox/*" -exec rm {} \;

# Verify structure
echo "Verifying structure..."
verify_structure() {
    local problems=0
    
    # Check shared modules
    if [ ! -f "shared/modules/NPCManagerV3.lua" ]; then
        echo "WARNING: NPCManagerV3.lua not found in shared/modules/"
        problems=$((problems + 1))
    fi
    
    # Check game1 structure
    for dir in data assets server client shared; do
        if [ ! -d "games/game1/src/$dir" ]; then
            echo "WARNING: games/game1/src/$dir directory missing"
            problems=$((problems + 1))
        fi
    done
    
    # Check Rojo config
    if [ ! -f "games/game1/default.project.json" ]; then
        echo "WARNING: games/game1/default.project.json missing"
        problems=$((problems + 1))
    fi
    
    return $problems
}

# Run verification
verify_structure
VERIFY_RESULT=$?

echo -e "\nCurrent structure:"
tree -L 4 games/
tree -L 2 shared/

if [ $VERIFY_RESULT -eq 0 ]; then
    echo -e "\nStructure update completed successfully!"
else
    echo -e "\nStructure update completed with $VERIFY_RESULT warnings."
fi

echo -e "\nNext steps:"
echo "1. Run 'rojo serve' in games/game1 directory"
echo "2. Verify game functionality"
echo "3. Check shared modules are loading correctly"

# Add this after the mkdir commands:
echo "Checking for NPCManagerV3.lua..."
if [ -f "games/game1/src/game_specific/server/NPCManagerV3.lua" ]; then
    echo "Found NPCManagerV3.lua in game1/server, moving to shared..."
    mv games/game1/src/game_specific/server/NPCManagerV3.lua shared/modules/
elif [ -f "src/server/NPCManagerV3.lua" ]; then
    echo "Found NPCManagerV3.lua in src/server, moving to shared..."
    mv src/server/NPCManagerV3.lua shared/modules/
fi

# Add verification
if [ ! -f "shared/modules/NPCManagerV3.lua" ]; then
    echo "ERROR: Could not locate NPCManagerV3.lua"
    echo "Please locate the file and move it to shared/modules/"
    exit 1
fi 