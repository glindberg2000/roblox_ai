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
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.storage_dir, self.assets_dir, self.thumbnails_dir, self.avatars_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directories initialized at {self.storage_dir}")

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

    async def store_avatar_image(self, user_id: str, url: str) -> str:
        """Store a player's avatar image."""
        save_path = self.avatars_dir / f"{user_id}.png"
        return await self.download_and_store_image(url, save_path)

    async def store_asset_thumbnail(self, asset_id: str, url: str) -> str:
        """Store an asset's thumbnail image."""
        save_path = self.thumbnails_dir / f"{asset_id}.png"
        return await self.download_and_store_image(url, save_path)

    async def store_asset_file(self, file: UploadFile, asset_id: str) -> Dict[str, str]:
        """Store an uploaded asset file (RBXMX) and return storage info."""
        try:
            timestamp = datetime.now().isoformat()
            original_filename = file.filename
            extension = Path(original_filename).suffix
            stored_filename = f"{asset_id}{extension}"
            file_path = self.assets_dir / stored_filename

            # Save the file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Parse RBXMX for components if applicable
            components = []
            if extension.lower() == '.rbxmx':
                components = self._parse_rbxmx_components(file_path)

            return {
                "filename": original_filename,
                "localPath": str(file_path.relative_to(self.storage_dir)),
                "uploadDate": timestamp,
                "components": components
            }

        except Exception as e:
            logger.error(f"Failed to store asset file: {e}")
            raise

    def _parse_rbxmx_components(self, file_path: Path) -> list:
        """Extract component information from RBXMX file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            components = set()
            for elem in root.findall(".//*[@class]"):
                components.add(elem.attrib['class'])
            return sorted(list(components))
        except Exception as e:
            logger.error(f"Failed to parse RBXMX components: {e}")
            return []

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
