import sqlite3
import os
import sys
from pathlib import Path

# Add api directory to path
api_dir = Path(__file__).parent.parent
sys.path.append(str(api_dir))

from app.config import SQLITE_DB_PATH
from letta_roblox.client import LettaRobloxClient

def cleanup_agents():
    """Clean up agents from both Letta server and local database"""
    print("Starting cleanup...")
    
    # 1. Delete from Letta server
    letta_client = LettaRobloxClient("http://localhost:8333")
    try:
        letta_client.delete_all_agents()
        print("✓ Cleared agents from Letta server")
    except Exception as e:
        print(f"! Failed to clear Letta agents: {e}")
    
    # 2. Clear local database
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as db:
            cursor = db.execute("DELETE FROM npc_agents")
            count = cursor.rowcount
            db.commit()
            print(f"✓ Cleared {count} agent mappings from local database")
    except Exception as e:
        print(f"! Failed to clear local database: {e}")

if __name__ == "__main__":
    cleanup_agents() 