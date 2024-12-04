import asyncio
import sys
from pathlib import Path

# Add api directory to path
api_dir = Path(__file__).parent.parent
sys.path.append(str(api_dir))

from app.image_utils import get_roblox_display_name
from app.database import store_player_description, get_player_description

async def test_player_info():
    """Test player info lookup and storage"""
    player_id = "962483389"  # greggytheegg's ID
    
    print("\nTesting player info for greggytheegg...")
    
    # 1. Get display name from Roblox
    print("\n1. Getting display name from Roblox...")
    display_name = await get_roblox_display_name(player_id)
    print(f"Display name: {display_name}")
    
    # 2. Store in database
    print("\n2. Storing in database...")
    store_player_description(
        player_id=player_id,
        description="Test description",
        display_name=display_name
    )
    
    # 3. Retrieve from database
    print("\n3. Retrieving from database...")
    player_info = get_player_description(player_id)
    print(f"Retrieved info: {player_info}")

if __name__ == "__main__":
    asyncio.run(test_player_info()) 