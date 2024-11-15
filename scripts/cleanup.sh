#!/bin/bash

# Exit on any error
set -e

echo "Starting cleanup..."

# Get the project root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$ROOT_DIR"

# Function to find and remove symlinks
cleanup_symlinks() {
    echo "Removing symlinks..."
    find . -type l ! -path "./roblox/*" -exec rm {} \;
}

# Function to check for duplicate files
check_duplicates() {
    echo "Checking for duplicate NPCManagerV3.lua..."
    find . -name "NPCManagerV3.lua" -type f | while read -r file; do
        echo "Found: $file"
    done
}

# Function to ensure correct file locations
ensure_correct_locations() {
    echo "Ensuring files are in correct locations..."
    
    # Ensure NPCManagerV3.lua is only in shared/modules
    if [ -f "games/game1/src/game_specific/server/NPCManagerV3.lua" ]; then
        echo "Moving NPCManagerV3.lua to shared/modules..."
        mv "games/game1/src/game_specific/server/NPCManagerV3.lua" "shared/modules/"
    fi
    
    # Create necessary directories if they don't exist
    mkdir -p shared/modules
    mkdir -p games/game1/src/{data,assets/npcs,game_specific/{server,client}}
}

# Function to verify structure
verify_structure() {
    echo "Verifying directory structure..."
    
    # Check shared modules
    if [ ! -f "shared/modules/NPCManagerV3.lua" ]; then
        echo "WARNING: NPCManagerV3.lua not found in shared/modules/"
    fi
    
    # Check game directories
    if [ ! -d "games/game1/src/game_specific/server" ]; then
        echo "WARNING: Game server directory missing"
    fi
    
    if [ ! -d "games/game1/src/game_specific/client" ]; then
        echo "WARNING: Game client directory missing"
    fi
}

# Main execution
echo "Starting cleanup process..."

cleanup_symlinks
check_duplicates
ensure_correct_locations
verify_structure

echo "Cleanup complete!"
echo ""
echo "Current structure:"
tree -L 4 games/
tree -L 2 shared/

echo ""
echo "Next steps:"
echo "1. Verify NPCManagerV3.lua is only in shared/modules/"
echo "2. Test Rojo serve in games/game1/"
echo "3. Verify game functionality" 