import sys
from pathlib import Path

# Add api directory to Python path
api_dir = Path(__file__).parent.parent
sys.path.append(str(api_dir))

from app.database import store_player_description, get_player_description

def test_player_descriptions():
    """Test player description storage and retrieval"""
    print("Testing player descriptions...")
    
    # Test data
    test_data = {
        "player_id": "test456",
        "description": "A test player avatar",
        "display_name": "TestPlayer"
    }
    
    try:
        # Store description
        store_player_description(**test_data)
        print("✓ Stored player description")
        
        # Retrieve description
        result = get_player_description(test_data["player_id"])
        print(f"Retrieved data: {result}")
        
        assert result["description"] == test_data["description"]
        assert result["display_name"] == test_data["display_name"]
        print("✓ Data verification passed")
        
    except Exception as e:
        print(f"! Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_player_descriptions() 