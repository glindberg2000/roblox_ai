import logging
from ..database import get_db

logger = logging.getLogger("migration_test")

def test_agent_mappings_migration():
    """Test that agent_mappings table was created correctly"""
    try:
        with get_db() as db:
            # Check table exists
            cursor = db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='agent_mappings'
            """)
            if not cursor.fetchone():
                logger.error("agent_mappings table not found!")
                return False

            # Check columns
            cursor = db.execute("PRAGMA table_info(agent_mappings)")
            columns = {col['name']: col for col in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'npc_id': 'INTEGER',
                'participant_id': 'TEXT',
                'agent_id': 'TEXT',
                'agent_type': 'TEXT',
                'created_at': 'TIMESTAMP'
            }

            for col_name, expected_type in expected_columns.items():
                if col_name not in columns:
                    logger.error(f"Missing column: {col_name}")
                    return False
                if expected_type not in columns[col_name]['type'].upper():
                    logger.error(f"Wrong type for {col_name}: expected {expected_type}, got {columns[col_name]['type']}")
                    return False

            # Check index exists
            cursor = db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_agent_mapping'
            """)
            if not cursor.fetchone():
                logger.error("Index idx_agent_mapping not found!")
                return False

            # Test insert
            try:
                db.execute('BEGIN')
                db.execute("""
                    INSERT INTO agent_mappings 
                    (npc_id, participant_id, agent_id, agent_type)
                    VALUES (1, 'test_participant', 'test_agent', 'letta')
                """)
                db.rollback()  # Don't actually insert test data
            except Exception as e:
                logger.error(f"Insert test failed: {e}")
                return False

            logger.info("Migration test passed successfully!")
            return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_agent_mappings_migration()
    exit(0 if success else 1) 