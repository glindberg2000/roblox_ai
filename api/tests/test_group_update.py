import requests
import sys

BASE_URL = "http://localhost:8000/letta/v1"

def test_group_update(action="join"):
    # Test data
    TEST_AGENT_ID = "agent-807e4d69-59a4-4f55-b0bb-ec85bf6e376b"  # Kaiden
    TEST_PLAYER = {
        "id": "962483389",
        "name": "greggytheegg"
    }

    print("\nTest Data:")
    print(f"Agent ID: {TEST_AGENT_ID}")
    print(f"Player: {TEST_PLAYER}")
    print(f"Action: {action}")
    
    if action == "purge":
        # Reset group to empty state
        response = requests.post(f"{BASE_URL}/npc/group/update", json={
            "npc_id": TEST_AGENT_ID,
            "player_id": "0",  # Dummy ID for purge
            "is_joining": True,
            "player_name": "PURGE",
            "purge": True  # New flag
        })
    else:
        # Normal join/leave
        response = requests.post(f"{BASE_URL}/npc/group/update", json={
            "npc_id": TEST_AGENT_ID,
            "player_id": TEST_PLAYER["id"],
            "is_joining": action == "join",
            "player_name": TEST_PLAYER["name"]
        })

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200
    print(f"Result: {response.json()}")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "join"
    test_group_update(action) 