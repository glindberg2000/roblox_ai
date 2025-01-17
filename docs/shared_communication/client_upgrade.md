# Client Upgrade Communication Log

## December 24, 2023 - Navigation Testing Enhancement

### @LettaDev - Initial Navigation Tool Update (v0.2.5)
Fixed the navigation tool with:
1. Fixed "LOCATION_API_URL undefined" error
2. Added proper connection handling with retries
3. Added timeouts to prevent hangs
4. Response format remains:
```python
{
    "status": "success",
    "message": "Found Pete's Merch Stand. Beginning navigation...",
    "coordinates": {
        "x": -12.0,
        "y": 18.9,
        "z": -127.0
    }
}
```

### @RobloxDev - Test Script Enhancement Requirements
To improve navigation testing with real NPC data:

1. Get Valid NPC Data:
```python
def get_test_npc():
    """Get Pete's NPC ID for navigation testing"""
    response = requests.get("http://localhost:7777/api/npcs?game_id=61")
    npcs = response.json()["npcs"]
    
    # Find Pete specifically since he has the merch stand
    pete = next((npc for npc in npcs 
                 if npc["displayName"] == "Pete" and 
                 "move" in npc["abilities"]), None)
    
    if not pete:
        raise Exception("Could not find Pete NPC for testing")
        
    return pete["npcId"]
```

2. Correct Chat Request Format:
```python
def send_test_chat(npc_id: str, message: str):
    request = {
        "npc_id": npc_id,
        "participant_id": "test_user_1",
        "message": message,
        "context": {
            "participant_type": "player",
            "participant_name": "TestUser"
        }
    }
    
    response = requests.post(
        "http://localhost:7777/letta/v1/chat",
        json=request
    )
    return response.json()
```

3. Navigation Test Function:
```python
def test_navigation():
    # Get Pete's NPC ID
    npc_id = get_test_npc()
    
    # Test navigation message
    response = send_test_chat(
        npc_id=npc_id,
        message="Can you take me to Pete's stand?"
    )
    
    # Validate response format
    assert response["action"]["type"] == "navigate"
    assert "coordinates" in response["action"]["data"]
    coords = response["action"]["data"]["coordinates"]
    assert all(k in coords for k in ["x", "y", "z"])
```

### Key Requirements:
1. Remove hardcoded NPC IDs
2. Remove interaction_id from initial requests
3. Match production request format exactly
4. Add proper validation of responses

### System Architecture Notes:
- Roblox Studio (Cloud) -> FastAPI (/letta/v1/chat) -> Docker Letta -> Location API -> OpenAI
- FastAPI runs on port 7777
- Docker Letta runs on localhost:8283
- Docker->Host communication uses host.docker.internal

### Current NPCs in Game 61:
- Pete (npcId: "693ec89f-40f1-4321-aef9-5aac428f478b")
  - Location: spawnPosition: {x:-12.5, y:18.0, z:-126.0}
  - Abilities: ["move", "chat", "initiate_chat", "follow", "unfollow", "run", "jump", "emote"]
- Oscar (npcId: "3cff63ac-9960-46bb-af7f-88e824d68dbe")
- Noobster (npcId: "0544b51c-1009-4231-ac6e-053626135ed4")
- Diamond (npcId: "8c9bba8d-4f9a-4748-9e75-1334e48e2e66")
- Goldie (npcId: "e43613f0-cc70-4e98-9b61-2a39fecfa443")
