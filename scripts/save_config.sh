#!/bin/bash

# Save pip requirements
source roblox/bin/activate
pip freeze > api/requirements.txt.temp

# Filter only direct dependencies from requirements.txt (lines 1-8)
cat > api/requirements.txt << EOL
fastapi
uvicorn
python-dotenv
pydantic
openai
python-multipart
pillow
requests
EOL

# Clean up
rm api/requirements.txt.temp

# Create required directories based on config.py (lines 9-26)
mkdir -p api/storage/assets
mkdir -p api/storage/thumbnails
mkdir -p api/storage/avatars
mkdir -p api/stored_images
mkdir -p api/stored_asset_images
mkdir -p src/assets
mkdir -p src/data

# Save directory structure to gitignore
cat > .gitignore << EOL
# Python virtual environment
roblox/
venv/
env/
.env

# Python cache
__pycache__/
*.py[cod]

# Storage directories
api/storage/
api/stored_images/
api/stored_asset_images/

# IDE settings
.vscode/
.idea/
EOL

echo "Configuration saved successfully!" 