import sqlite3
import os
import sys
from pathlib import Path
import argparse
import subprocess

# Add api directory to path
api_dir = Path(__file__).parent.parent
sys.path.append(str(api_dir))

from app.config import SQLITE_DB_PATH
from letta_roblox.client import LettaRobloxClient

def cleanup_database():
    """Clean up agent mappings from local database"""
    print("Starting database cleanup...")
    
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as db:
            # First show current mappings
            cursor = db.execute("""
                SELECT npc_id, participant_id, letta_agent_id, created_at 
                FROM npc_agents 
                ORDER BY created_at DESC
            """)
            mappings = cursor.fetchall()
            
            if mappings:
                print("\nCurrent agent mappings:")
                for m in mappings:
                    print(f"NPC: {m[0]}")
                    print(f"Participant: {m[1]}")
                    print(f"Agent ID: {m[2]}")
                    print(f"Created: {m[3]}\n")
                
                if input("Delete these mappings? (y/N) ").lower() == 'y':
                    cursor = db.execute("DELETE FROM npc_agents")
                    count = cursor.rowcount
                    db.commit()
                    print(f"✓ Cleared {count} agent mappings from database")
            else:
                print("No agent mappings found in database")
                
    except Exception as e:
        print(f"! Failed to clean database: {e}")

def list_letta_agents():
    """List agents using letta-manage"""
    subprocess.run(["letta-manage", "--server", "http://localhost:8283", "list"])

def delete_all_letta_agents():
    """Delete all agents using letta-manage"""
    subprocess.run(["letta-manage", "--server", "http://localhost:8283", "delete-all"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--letta", action="store_true", 
                       help="Also clean up Letta server agents")
    args = parser.parse_args()
    
    cleanup_database()
    if args.letta:
        # Show current agents
        list_letta_agents()
        
        # Ask to delete
        if input("\nDelete all agents? (y/N) ").lower() == 'y':
            delete_all_letta_agents() 