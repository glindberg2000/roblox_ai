import click
from .db import init_db
from .db.migrations import check_migration_status
import sqlite3
from .config import SQLITE_DB_PATH

@click.group()
def cli():
    """Database management commands"""
    pass

@cli.command()
def migrate():
    """Run database migrations"""
    print("Running migrations...")
    init_db()
    print("Migrations complete!")

@cli.command()
def check():
    """Check database status"""
    check_migration_status()
    with sqlite3.connect(SQLITE_DB_PATH) as db:
        cursor = db.execute("SELECT npc_id, display_name, enabled FROM npcs")
        print("\nNPC Status:")
        for row in cursor:
            print(f"NPC: {row[1]} ({row[0]}) - Enabled: {row[2]}")

if __name__ == '__main__':
    cli() 