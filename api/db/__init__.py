from .migrations import run_migrations

def init_db():
    """Initialize database and run migrations"""
    run_migrations()
