import pytest
from ..database import (
    get_db, 
    get_npc_context, 
    create_agent_mapping, 
    get_agent_mapping
)
from ..models import AgentMapping
import json

def test_npc_context_retrieval():
    """Test getting NPC context with asset info"""
    with get_db() as db:
        # First create test data
        db.executescript("""
            INSERT INTO games (id, title, slug) VALUES (1, 'Test Game', 'test-game');
            
            INSERT INTO assets (game_id, asset_id, name, description) 
            VALUES (1, 'test-asset', 'Test Asset', 'A test asset description');
            
            INSERT INTO npcs (
                id, game_id, npc_id, display_name, asset_id, 
                system_prompt, abilities
            ) VALUES (
                1, 1, 'test-npc', 'Test NPC', 'test-asset',
                'I am a test NPC', '["ability1", "ability2"]'
            );
        """)
        db.commit()
        
        # Test context retrieval
        context = get_npc_context(1)
        assert context is not None
        assert context["display_name"] == "Test NPC"
        assert context["system_prompt"] == "I am a test NPC"
        assert context["abilities"] == ["ability1", "ability2"]
        assert context["description"] == "A test asset description"

def test_agent_mapping_crud():
    """Test Create, Read, Update, Delete operations for agent mappings"""
    with get_db() as db:
        # Create
        mapping = create_agent_mapping(
            npc_id=1,
            participant_id="test-participant",
            agent_id="test-agent-id"
        )
        assert mapping.npc_id == 1
        assert mapping.agent_id == "test-agent-id"
        
        # Read
        retrieved = get_agent_mapping(1, "test-participant")
        assert retrieved is not None
        assert retrieved.agent_id == "test-agent-id"
        
        # Delete
        db.execute("""
            DELETE FROM agent_mappings 
            WHERE npc_id = ? AND participant_id = ?
        """, (1, "test-participant"))
        db.commit()
        
        # Verify deleted
        assert get_agent_mapping(1, "test-participant") is None

def cleanup_test_data():
    """Clean up test data"""
    with get_db() as db:
        db.executescript("""
            DELETE FROM agent_mappings;
            DELETE FROM npcs WHERE game_id = 1;
            DELETE FROM assets WHERE game_id = 1;
            DELETE FROM games WHERE id = 1;
        """)
        db.commit()

if __name__ == "__main__":
    try:
        test_npc_context_retrieval()
        test_agent_mapping_crud()
        print("All tests passed!")
    finally:
        cleanup_test_data() 