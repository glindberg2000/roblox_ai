import sqlite3
from pathlib import Path
import json

def verify_database():
    """Verify database structure and contents"""
    db_path = Path(__file__).parent.parent / "db" / "game_data.db"
    
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        
        # Check schema
        print("\nCurrent Database Schema:")
        cursor = db.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        for table in cursor.fetchall():
            print(f"\n{table['sql']}")
        
        # Check data in each table
        print("\nData Summary:")
        
        # Check assets
        cursor = db.execute("SELECT * FROM assets")
        assets = cursor.fetchall()
        print(f"\nAssets ({len(assets)}):")
        for asset in assets:
            print(f"  {dict(asset)}")
        
        # Check NPCs
        cursor = db.execute("SELECT * FROM npcs")
        npcs = cursor.fetchall()
        print(f"\nNPCs ({len(npcs)}):")
        for npc in npcs:
            print(f"  {dict(npc)}")
        
        # Check foreign key relationships
        print("\nChecking NPC-Asset relationships:")
        cursor = db.execute("""
            SELECT n.npc_id, n.display_name, n.asset_id, a.name as asset_name
            FROM npcs n
            LEFT JOIN assets a ON n.asset_id = a.asset_id
        """)
        relationships = cursor.fetchall()
        for rel in relationships:
            if rel['asset_name'] is None:
                print(f"  WARNING: Orphaned NPC {rel['display_name']} -> missing asset {rel['asset_id']}")
            else:
                print(f"  OK: NPC {rel['display_name']} -> Asset {rel['asset_name']}")

if __name__ == "__main__":
    verify_database() 