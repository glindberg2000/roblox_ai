from ..database import get_db

def update_agent_mappings():
    """Update agent mappings to use UUID instead of numeric ID"""
    with get_db() as db:
        # Get mapping of id to npc_id
        cursor = db.execute("SELECT id, npc_id FROM npcs")
        id_to_uuid = {row['id']: row['npc_id'] for row in cursor.fetchall()}
        
        # Update agent_mappings
        cursor = db.execute("SELECT * FROM agent_mappings")
        for row in cursor.fetchall():
            if str(row['npc_id']).isdigit():  # If it's a numeric ID
                uuid = id_to_uuid.get(row['npc_id'])
                if uuid:
                    db.execute("""
                        UPDATE agent_mappings 
                        SET npc_id = ? 
                        WHERE id = ?
                    """, (uuid, row['id']))
        
        db.commit()

if __name__ == "__main__":
    update_agent_mappings() 