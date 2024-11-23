import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migration_runner")

def run_migration(migration_name: str, rollback: bool = False):
    try:
        # Import the migration module
        migration = __import__(f"app.migrations.{migration_name}", fromlist=[''])
        
        if rollback:
            if hasattr(migration, 'rollback_spawn_positions'):
                logger.info(f"Rolling back migration: {migration_name}")
                migration.rollback_spawn_positions()
            else:
                logger.error(f"No rollback function found in {migration_name}")
                return False
        else:
            if hasattr(migration, 'migrate_spawn_positions'):
                logger.info(f"Running migration: {migration_name}")
                migration.migrate_spawn_positions()
            else:
                logger.error(f"No migration function found in {migration_name}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.migrations.run_migrations <migration_name> [--rollback]")
        sys.exit(1)
        
    migration_name = sys.argv[1]
    rollback = "--rollback" in sys.argv
    
    success = run_migration(migration_name, rollback)
    sys.exit(0 if success else 1) 