#!/bin/bash

# Configuration
REPO_DIR=/home/plato/dev/roblox
BACKUP_DIR=/media/sf_letta_backups/config_backups
DATE=$(date +%Y%m%d_%H%M%S)

# Backup config.py with timestamp
cp "$REPO_DIR/api/app/config.py" "$BACKUP_DIR/config_$DATE.py"

# Keep only last 5 backups
ls -t "$BACKUP_DIR"/config_*.py | tail -n +6 | xargs -r rm 