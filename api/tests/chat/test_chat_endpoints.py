# tests/test_chat_endpoints.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
from datetime import datetime
import os

client = TestClient(app)

# Test data
NPC_TEST_DATA = {
    "npc_id": "test_npc_1",
    "display_name": "Test NPC",
    "system_prompt": "You are a friendly test NPC."
}

PLAYER_TEST_DATA = {
    "player_id": "test_player_1",
    "name": "Test Player"
}

@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ["TESTING"] = "1"
    yield
    os.environ.pop("TESTING", None)

@pytest.fixture
def v3_chat_payload():
    return {
        "message": "Hello there!",
        "player_id": PLAYER_TEST_DATA["player_id"],
        "npc_id": NPC_TEST_DATA["npc_id"],
        "npc_name": NPC_TEST_DATA["display_name"],
        "system_prompt": NPC_TEST_DATA["system_prompt"],
        "context": {
            "player_name": PLAYER_TEST_DATA["name"],
            "is_new_conversation": True,
            "time_since_last_interaction": "N/A",
            "nearby_players": [],
            "npc_location": "spawn"
        },
        "perception": {
            "visible_objects": [],
            "visible_players": [],
            "memory": []
        },
        "limit": 200
    }

@pytest.fixture
def v4_chat_payload():
    return {
        "message": "Hello there!",
        "initiator_id": PLAYER_TEST_DATA["player_id"],
        "target_id": NPC_TEST_DATA["npc_id"],
        "conversation_type": "npc_user",
        "system_prompt": NPC_TEST_DATA["system_prompt"],
        "context": {
            "initiator_name": PLAYER_TEST_DATA["name"],
            "target_name": NPC_TEST_DATA["display_name"],
            "is_new_conversation": True
        }
    }

def test_v3_chat_endpoint(v3_chat_payload):
    """Test the V3 chat endpoint"""
    response = client.post("/robloxgpt/v3", json=v3_chat_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "action" in data
    assert data["action"]["type"] in ["follow", "unfollow", "stop_talking", "none"]
    
    # Test response format
    assert isinstance(data["message"], str)
    assert isinstance(data["action"], dict)
    assert "type" in data["action"]
    assert isinstance(data["action"]["type"], str)

def test_v4_chat_endpoint(v4_chat_payload):
    """Test the V4 chat endpoint"""
    response = client.post("/v4/chat", json=v4_chat_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data
    assert "action" in data
    assert "metadata" in data
    
    # Test response format
    assert isinstance(data["conversation_id"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["action"], dict)
    assert data["action"]["type"] in ["follow", "unfollow", "stop_talking", "none"]

def test_v4_conversation_flow():
    """Test a complete conversation flow in V4"""
    # Start conversation
    payload = {
        "message": "Hello!",
        "initiator_id": "npc1",
        "target_id": "player1",
        "conversation_type": "npc_user",
        "system_prompt": "You are a friendly NPC."
    }
    
    response1 = client.post("/v4/chat", json=payload)
    assert response1.status_code == 200
    conv_id = response1.json()["conversation_id"]
    
    # Continue conversation
    payload["conversation_id"] = conv_id
    payload["message"] = "How are you?"
    response2 = client.post("/v4/chat", json=payload)
    assert response2.status_code == 200
    assert response2.json()["conversation_id"] == conv_id
    
    # End conversation
    response3 = client.delete(f"/v4/conversations/{conv_id}")
    assert response3.status_code == 200

def test_v4_npc_to_npc_conversation():
    """Test NPC-to-NPC conversation in V4"""
    payload = {
        "message": "Hello fellow NPC!",
        "initiator_id": "npc1",
        "target_id": "npc2",
        "conversation_type": "npc_npc",
        "system_prompt": "You are a friendly NPC talking to another NPC."
    }
    
    response = client.post("/v4/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verify response format
    assert "conversation_id" in data
    assert "message" in data
    assert "action" in data
    assert isinstance(data["metadata"], dict)

def test_error_handling():
    """Test error handling in both endpoints"""
    # V3 invalid payload
    response = client.post("/robloxgpt/v3", json={})
    assert response.status_code == 400
    
    # V4 invalid payload
    response = client.post("/v4/chat", json={})
    assert response.status_code == 422
    
    # V4 invalid conversation type
    payload = {
        "message": "Hello!",
        "initiator_id": "npc1",
        "target_id": "player1",
        "conversation_type": "invalid_type",
        "system_prompt": "You are a friendly NPC."
    }
    response = client.post("/v4/chat", json=payload)
    assert response.status_code == 422
    error_detail = response.json()["detail"][0]
    assert error_detail["loc"] == ["body", "conversation_type"]
    assert "Input should be 'npc_user', 'npc_npc' or 'group'" in error_detail["msg"]

def test_v4_metrics():
    """Test V4 metrics endpoint"""
    response = client.get("/v4/metrics")
    assert response.status_code == 200
    data = response.json()
    
    assert "conversation_metrics" in data
    metrics = data["conversation_metrics"]
    assert isinstance(metrics["total_conversations"], int)
    assert isinstance(metrics["successful_conversations"], int)
    assert isinstance(metrics["failed_conversations"], int)
    assert isinstance(metrics["average_duration"], (int, float))

# Integration tests
def test_cross_version_compatibility():
    """Test that V3 and V4 can coexist without interference"""
    # Make V3 request
    v3_payload = {
        "message": "Hello from V3!",
        "player_id": "test_player",
        "npc_id": "test_npc",
        "npc_name": "Test NPC",
        "system_prompt": "You are a test NPC.",
    }
    v3_response = client.post("/robloxgpt/v3", json=v3_payload)
    assert v3_response.status_code == 200

    # Make V4 request
    v4_payload = {
        "message": "Hello from V4!",
        "initiator_id": "test_player",
        "target_id": "test_npc",
        "conversation_type": "npc_user",
        "system_prompt": "You are a test NPC."
    }
    v4_response = client.post("/v4/chat", json=v4_payload)
    assert v4_response.status_code == 200

    # Verify responses are properly formatted
    assert "message" in v3_response.json()
    assert "conversation_id" in v4_response.json()