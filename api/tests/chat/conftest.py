# tests/conftest.py

import pytest
import os
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_openai_key():
    """Mock OpenAI API key for tests"""
    os.environ["OPENAI_API_KEY"] = "mock-key-for-testing"

@pytest.fixture(scope="session")
def test_npc():
    """Test NPC data"""
    return {
        "id": "test_npc_1",
        "display_name": "Test NPC",
        "system_prompt": "You are a friendly test NPC."
    }

@pytest.fixture(scope="session")
def test_player():
    """Test player data"""
    return {
        "id": "test_player_1",
        "name": "Test Player"
    }

@pytest.fixture
def mock_ai_response():
    """Mock AI response"""
    return {
        "message": "Hello! How can I help you?",
        "action": {
            "type": "none",
            "data": None
        },
        "internal_state": {}
    }