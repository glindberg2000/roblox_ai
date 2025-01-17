from api.app.database import get_db

def verify_database():
    """Check current database state"""
    with get_db() as db:
        print("\n=== Database State ===")
        
        # Check games
        cursor = db.execute("SELECT * FROM games")
        games = cursor.fetchall()
        print("\nGames:")
        for game in games:
            print(f"- {game['title']} (ID: {game['id']}, slug: {game['slug']})")
            
            # Count assets and NPCs for this game
            assets = db.execute("""
                SELECT COUNT(*) as count FROM assets WHERE game_id = ?
            """, (game['id'],)).fetchone()['count']
            
            npcs = db.execute("""
                SELECT COUNT(*) as count FROM npcs WHERE game_id = ?
            """, (game['id'],)).fetchone()['count']
            
            print(f"  Assets: {assets}")
            print(f"  NPCs: {npcs}")
            
            # Show asset details
            print("\n  Assets:")
            cursor = db.execute("SELECT * FROM assets WHERE game_id = ?", (game['id'],))
            for asset in cursor.fetchall():
                print(f"    - {asset['name']} (ID: {asset['asset_id']})")
            
            # Show NPC details
            print("\n  NPCs:")
            cursor = db.execute("SELECT * FROM npcs WHERE game_id = ?", (game['id'],))
            for npc in cursor.fetchall():
                print(f"    - {npc['display_name']} (ID: {npc['npc_id']})")

if __name__ == "__main__":
    verify_database() 