import os
import sys
from pathlib import Path

print(f"Current working directory: {os.getcwd()}")
print(f"Python path before: {sys.path}")

# Add the current directory to Python path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
print(f"Added to path: {current_dir}")
print(f"Python path after: {sys.path}")

try:
    from app.database import init_db
    print("Successfully imported database")
    from app.utils import load_json_database
    print("Successfully imported utils")
except ImportError as e:
    print(f"Import error: {e}") 