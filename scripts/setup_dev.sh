#!/bin/bash

# Create and activate virtual environment
python3 -m venv roblox
source roblox/bin/activate

# Install requirements
pip install -r api/requirements.txt

# Create necessary directories
mkdir -p api/storage/assets
mkdir -p api/storage/thumbnails
mkdir -p api/storage/avatars
mkdir -p api/stored_images
mkdir -p api/stored_asset_images 