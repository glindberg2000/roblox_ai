import logging
from ..database import get_db, get_npc_context, create_agent_mapping, get_agent_mapping
from ..letta_router import letta_client
from pydantic import BaseModel
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oscar_test")

def get_oscar_id():
    """Get Oscar's NPC ID from the database"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT id 
            FROM npcs 
            WHERE display_name LIKE '%Oscar%'
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result['id'] if result else None

def test_oscar_initial_chat():
    """Initial conversation establishing Fred's character"""
    oscar_id = get_oscar_id()
    participant_id = "fred_123"
    participant_name = "Fred"

    try:
        # First check if we already have an agent
        agent_mapping = get_agent_mapping(
            npc_id=oscar_id,
            participant_id=participant_id
        )
        
        if agent_mapping:
            logger.info(f"Found existing agent mapping: {agent_mapping}")
            agent_id = agent_mapping.agent_id
        else:
            # Only create new agent if one doesn't exist
            logger.info("Creating new agent...")
            oscar_context = get_npc_context(oscar_id)
            agent = letta_client.create_agent(
                npc_type="npc",
                initial_memory={
                    "human": f"I am {participant_name}, a new visitor.",
                    "persona": oscar_context["system_prompt"],
                    "description": oscar_context["description"],
                    "abilities": oscar_context["abilities"],
                    "display_name": oscar_context["display_name"]
                }
            )
            
            agent_mapping = create_agent_mapping(
                npc_id=oscar_id,
                participant_id=participant_id,
                agent_id=agent["id"]
            )
            agent_id = agent["id"]

        # Initial conversation with more personal details
        messages = [
            "Hi there! I'm new around here. I just moved from the farming district.",
            "I used to work with my family growing vegetables, but I'm looking for more adventure now!",
            "I heard there might be some interesting quests in this area. I'm pretty good with a sword from protecting our farm from wild animals."
        ]

        for msg in messages:
            logger.info(f"Sending message: {msg}")
            response = letta_client.send_message(agent_id, msg)
            logger.info(f"Response from Oscar: {response}")

    except Exception as e:
        logger.error(f"Error in initial chat: {e}")
        raise

def test_oscar_memory():
    """Test if Oscar remembers details about Fred without explicit reminders"""
    participant_id = "fred_123"
    oscar_id = get_oscar_id()
    
    try:
        agent_mapping = get_agent_mapping(
            npc_id=oscar_id,
            participant_id=participant_id
        )
        
        if not agent_mapping:
            logger.error("Could not find existing agent mapping")
            return
            
        logger.info(f"Found existing agent mapping: {agent_mapping}")
        
        # Test memory without mentioning name or background
        message = "So, what do you remember about me and my background?"
        logger.info(f"Sending message: {message}")
        
        response = letta_client.send_message(
            agent_mapping.agent_id,
            message
        )
        
        logger.info(f"Response from Oscar: {response}")
        
    except Exception as e:
        logger.error(f"Error in memory test: {e}")
        raise

if __name__ == "__main__":
    # First run the initial conversation
    test_oscar_initial_chat()
    
    # Then test memory after a brief pause
    logger.info("Waiting 5 seconds before testing memory...")
    time.sleep(5)
    test_oscar_memory()