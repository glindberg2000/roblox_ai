import requests

# Test chat endpoint
response = requests.post(
    "http://localhost:7777/letta/v1/chat",
    json={
        "npc_id": "test-npc-1",
        "participant_id": "player-123",
        "message": "Hello!",
        "system_prompt": "I am a friendly merchant NPC.",
        "context": {
            "location": "market square",
            "time_of_day": "morning"
        }
    }
)

print(response.json()) 