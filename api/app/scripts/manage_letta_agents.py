from ..database import get_db, get_agent_mapping
from ..letta_roblox.client import LettaRobloxClient
import argparse
import sys
import requests

letta_client = LettaRobloxClient("http://localhost:8283")

def check_letta_server():
    """Verify Letta server is running"""
    try:
        response = requests.get("http://localhost:8283/health")
        response.raise_for_status()
        print("Letta server is running")
        return True
    except Exception as e:
        print(f"Error: Letta server not available at localhost:8283")
        print(f"Make sure the Letta server is running locally")
        return False

def list_agents():
    """List all agent mappings and their Letta agents"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT * FROM npc_agents 
            ORDER BY created_at DESC
        """)
        mappings = cursor.fetchall()
        
        print("\nAgent Mappings:")
        print("-" * 80)
        for m in mappings:
            print(f"NPC ID: {m['npc_id']}")
            print(f"Participant ID: {m['participant_id']}")
            print(f"Letta Agent ID: {m['letta_agent_id']}")
            print(f"Created: {m['created_at']}")
            
            # Get agent details from Letta
            details = letta_client.get_agent_details(m['letta_agent_id'])
            if details.get('memory'):
                print("\nMemory:")
                print(f"Persona: {details['memory'].get('persona', 'Not set')}")
                print(f"Human: {details['memory'].get('human', 'Not set')}")
            
            print("-" * 80)
        
        return mappings

def delete_all_agents():
    """Delete all agent mappings and their Letta agents"""
    mappings = list_agents()
    
    if input("\nAre you sure you want to delete all agents? (y/N) ").lower() != 'y':
        print("Aborted.")
        return
        
    with get_db() as db:
        for m in mappings:
            try:
                # Delete from Letta
                letta_client.delete_agent(m['letta_agent_id'])
                print(f"Deleted Letta agent: {m['letta_agent_id']}")
                
                # Delete mapping
                db.execute("DELETE FROM npc_agents WHERE id = ?", (m['id'],))
                print(f"Deleted mapping for NPC {m['npc_id']}")
            except Exception as e:
                print(f"Error deleting agent {m['letta_agent_id']}: {e}")
        
        db.commit()
    print("\nAll agents deleted.")

def cleanup_stale_mappings():
    """Remove mappings where Letta agent no longer exists"""
    with get_db() as db:
        cursor = db.execute("SELECT * FROM npc_agents")
        mappings = cursor.fetchall()
        
        cleaned = 0
        for m in mappings:
            try:
                details = letta_client.get_agent_details(m['letta_agent_id'])
                if not details:
                    db.execute("DELETE FROM npc_agents WHERE id = ?", (m['id'],))
                    print(f"Removed stale mapping for agent {m['letta_agent_id']}")
                    cleaned += 1
            except Exception:
                db.execute("DELETE FROM npc_agents WHERE id = ?", (m['id'],))
                print(f"Removed stale mapping for agent {m['letta_agent_id']}")
                cleaned += 1
        
        db.commit()
        print(f"\nCleaned up {cleaned} stale mappings")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manage Letta agents')
    parser.add_argument('action', choices=['list', 'delete-all', 'cleanup'], 
                      help='Action to perform')
    
    args = parser.parse_args()
    
    if not check_letta_server():
        sys.exit(1)
    
    if args.action == 'list':
        list_agents()
    elif args.action == 'delete-all':
        delete_all_agents()
    elif args.action == 'cleanup':
        cleanup_stale_mappings() 