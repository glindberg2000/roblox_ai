import sqlite3
import os

def init_db():
    # Read schema file
    with open('db/schema.sql', 'r') as f:
        schema = f.read()
    
    # Connect and create tables
    with sqlite3.connect('db/game_data.db') as db:
        db.executescript(schema)
        
        # Read and execute migrations
        migrations_dir = 'db/migrations'
        for file in sorted(os.listdir(migrations_dir)):
            if file.endswith('.sql'):
                with open(os.path.join(migrations_dir, file), 'r') as f:
                    db.executescript(f.read())

if __name__ == "__main__":
    init_db() 