from ..database import get_db
import logging

logger = logging.getLogger("migration_verify")

def verify_spawn_positions():
    """Verify spawn position migration"""
    with get_db() as db:
        # Check column existence
        cursor = db.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='npcs'
        """)
        table_def = cursor.fetchone()['sql']
        logger.info(f"Table definition: {table_def}")
        
        # Check data integrity
        cursor = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN spawn_x IS NULL OR spawn_y IS NULL OR spawn_z IS NULL THEN 1 ELSE 0 END) as null_coords,
                SUM(CASE WHEN spawn_position IS NULL THEN 1 ELSE 0 END) as null_json
            FROM npcs
        """)
        stats = cursor.fetchone()
        
        logger.info(f"""
        Migration Statistics:
        - Total NPCs: {stats['total']}
        - NPCs with NULL coordinates: {stats['null_coords']}
        - NPCs with NULL JSON: {stats['null_json']}
        """)
        
        return stats['null_coords'] == 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    verify_spawn_positions() 