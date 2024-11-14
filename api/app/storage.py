# api/app/storage.py

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from fastapi import UploadFile
import xml.etree.ElementTree as ET
import requests
from io import BytesIO
from PIL import Image
from .config import STORAGE_DIR, ASSETS_DIR, THUMBNAILS_DIR, AVATARS_DIR

logger = logging.getLogger("file_manager")

class FileStorageManager:
    def __init__(self):
        self.storage_dir = STORAGE_DIR
        self.assets_dir = ASSETS_DIR
        self.thumbnails_dir = THUMBNAILS_DIR
        self.avatars_dir = AVATARS_DIR
        
        # Ensure directories exist
        for directory in [self.storage_dir, self.assets_dir, 
                         self.thumbnails_dir, self.avatars_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def store_asset_file(self, file: UploadFile, asset_type: str) -> dict:
        """Store an asset file in the appropriate Roblox assets subdirectory."""
        try:
            # Get original filename and standardize it
            original_name = os.path.splitext(file.filename)[0].lower()
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            # Standardize filename
            safe_filename = ''.join(c if c.isalnum() or c == '_' else '_' 
                                  for c in original_name.replace(' ', '_'))
            
            if file_ext not in ['.rbxm', '.rbxmx']:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Create type directory if it doesn't exist
            type_dir = self.assets_dir / asset_type.lower()
            type_dir.mkdir(exist_ok=True)
            
            # Store in appropriate directory
            file_path = type_dir / f"{safe_filename}{file_ext}"
            
            logger.info(f"Attempting to save file to: {file_path}")
            
            # Save the file
            with open(file_path, 'wb') as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"Successfully stored asset file at: {file_path}")
            
            return {
                "path": str(file_path),
                "filename": file_path.name,
                "size": file_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Error storing asset file: {e}")
            raise

    async def store_avatar_image(self, user_id: str, url: str) -> str:
        """Store a player's avatar image."""
        save_path = self.avatars_dir / f"{user_id}.png"
        return await self.download_and_store_image(url, save_path)

    async def store_asset_thumbnail(self, asset_id: str, url: str) -> str:
        """Store an asset's thumbnail image."""
        save_path = self.thumbnails_dir / f"{asset_id}.png"
        return await self.download_and_store_image(url, save_path)

    async def download_and_store_image(self, url: str, save_path: Path) -> str:
        """Download an image from URL and store it locally."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image.save(save_path)
            return str(save_path)
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            raise

    def get_avatar_path(self, user_id: str) -> Optional[Path]:
        """Get path to stored avatar image."""
        path = self.avatars_dir / f"{user_id}.png"
        return path if path.exists() else None

    def get_thumbnail_path(self, asset_id: str) -> Optional[Path]:
        """Get path to stored thumbnail image."""
        path = self.thumbnails_dir / f"{asset_id}.png"
        return path if path.exists() else None

    def get_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get path to stored asset file."""
        for ext in ['.rbxmx', '.rbxm']:
            path = self.assets_dir / f"{asset_id}{ext}"
            if path.exists():
                return path
        return None

    async def cleanup(self) -> Tuple[int, int, int]:
        """Clean up unused files and return count of deleted files."""
        # Implementation of cleanup logic
        pass

    async def delete_asset_files(self, asset_id: str) -> None:
        """Delete all files associated with an asset."""
        try:
            # Delete thumbnail
            thumbnail_path = self.thumbnails_dir / f"{asset_id}.png"
            if thumbnail_path.exists():
                thumbnail_path.unlink()

            # Delete asset file (try both .rbxmx and .rbxm extensions)
            for ext in ['.rbxmx', '.rbxm']:
                asset_path = self.assets_dir / f"{asset_id}{ext}"
                if asset_path.exists():
                    asset_path.unlink()

            logger.info(f"Successfully deleted files for asset {asset_id}")
        except Exception as e:
            logger.error(f"Error deleting asset files: {e}")
            raise
