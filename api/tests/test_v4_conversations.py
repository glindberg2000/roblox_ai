import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.ai_handler import AIHandler
from app.conversation_managerV2 import ConversationManagerV2, Participant
from datetime import datetime, timedelta
from app.models import NPCResponseV3, NPCAction

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def conversation_manager():
    return ConversationManagerV2()

@pytest.fixture
def ai_handler():
    return AIHandler(api_key="test_key")

class TestNPCConversations:
    def test_create_npc_conversation(self, conversation_manager):
        # Test creating an NPC-NPC conversation
        npc1 = Participant(id="npc1", type="npc", name="NPC 1")
        npc2 = Participant(id="npc2", type="npc", name="NPC 2")
        
        conv_id = conversation_manager.create_conversation(
            type="npc_npc",
            participant1=npc1,
            participant2=npc2
        )
        
        assert conv_id is not None
        assert conv_id in conversation_manager.conversations
        
        conv = conversation_manager.conversations[conv_id]
        assert conv.type == "npc_npc"
        assert len(conv.participants) == 2
        assert conv.participants[npc1.id].name == "NPC 1"
        assert conv.participants[npc2.id].name == "NPC 2"

    def test_add_message_to_conversation(self, conversation_manager):
        # Test adding messages to a conversation
        npc1 = Participant(id="npc1", type="npc", name="NPC 1")
        npc2 = Participant(id="npc2", type="npc", name="NPC 2")
        
        conv_id = conversation_manager.create_conversation(
            type="npc_npc",
            participant1=npc1,
            participant2=npc2
        )
        
        success = conversation_manager.add_message(
            conv_id,
            npc1.id,
            "Hello NPC 2!"
        )
        
        assert success
        conv = conversation_manager.conversations[conv_id]
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello NPC 2!"
        assert conv.messages[0].sender_id == npc1.id

    def test_conversation_expiry(self, conversation_manager):
        # Test conversation cleanup after expiry
        npc1 = Participant(id="npc1", type="npc", name="NPC 1")
        npc2 = Participant(id="npc2", type="npc", name="NPC 2")
        
        conv_id = conversation_manager.create_conversation(
            type="npc_npc",
            participant1=npc1,
            participant2=npc2
        )
        
        # Manually set last_update to trigger expiry
        conv = conversation_manager.conversations[conv_id]
        conv.last_update = datetime.now() - timedelta(minutes=31)
        
        # Run cleanup
        cleaned = conversation_manager.cleanup_expired()
        assert cleaned == 1
        assert conv_id not in conversation_manager.conversations

@pytest.mark.asyncio
class TestAIHandler:
    async def test_parallel_responses(self, ai_handler):
        # Test parallel processing of AI responses
        requests = [
            {
                "messages": [{"role": "user", "content": "Hello"}],
                "system_prompt": "You are a helpful assistant",
                "max_tokens": 100
            },
            {
                "messages": [{"role": "user", "content": "Hi there"}],
                "system_prompt": "You are a friendly NPC",
                "max_tokens": 100
            }
        ]
        
        responses = await ai_handler.process_parallel_responses(requests)
        assert len(responses) == 2
        assert all(isinstance(r, NPCResponseV3) for r in responses)

    async def test_rate_limiting(self, ai_handler):
        # Test rate limiting of AI requests
        start_time = datetime.now()
        
        requests = [
            {
                "messages": [{"role": "user", "content": f"Message {i}"}],
                "system_prompt": "You are a helpful assistant",
                "max_tokens": 50
            }
            for i in range(10)  # More than max_parallel_requests
        ]
        
        responses = await ai_handler.process_parallel_responses(requests)
        duration = (datetime.now() - start_time).total_seconds()
        
        assert len(responses) == 10
        # Should take longer due to rate limiting
        assert duration > 1.0

@pytest.mark.asyncio
class TestEndpoints:
    async def test_v4_conversation_endpoint(self, test_client):
        response = test_client.post(
            "/robloxgpt/v4",
            json={
                "conversation_id": "test_conv",
                "message": "Hello NPC!",
                "initiator_id": "player1",
                "target_id": "npc1",
                "conversation_type": "npc_user",
                "system_prompt": "You are a helpful NPC"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "action" in data

    async def test_conversation_metrics(self, test_client):
        # Make several requests to test metrics
        for _ in range(3):
            test_client.post(
                "/robloxgpt/v4",
                json={
                    "conversation_id": "test_conv",
                    "message": "Hello!",
                    "initiator_id": "player1",
                    "target_id": "npc1",
                    "conversation_type": "npc_user",
                    "system_prompt": "You are a helpful NPC"
                }
            )
        
        # Get metrics (assuming we add a metrics endpoint)
        response = test_client.get("/metrics/conversations")
        assert response.status_code == 200
        metrics = response.json()
        
        assert metrics["total_conversations"] == 3
        assert metrics["successful_conversations"] > 0
        assert "average_duration" in metrics 