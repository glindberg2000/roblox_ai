from . import run_migrations, check_migration_status

if __name__ == "__main__":
    print("Running migrations...")
    run_migrations()
    print("\nChecking migration status...")
    check_migration_status() 