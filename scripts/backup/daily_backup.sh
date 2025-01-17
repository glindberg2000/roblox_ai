#!/bin/bash

# Configuration
REPO_DIR=/home/plato/dev/roblox
BACKUP_DIR=/media/sf_letta_backups/roblox_backups
DATE=$(date +%Y%m%d_%H%M%S)
MAX_BACKUPS=7  # Keep a week's worth of backups
EMAIL="realcryptoplato@gmail.com"
DISCORD_WEBHOOK="***REMOVED***"


# Notification function
notify() {
    local title="$1"
    local message="$2"
    curl -H "Content-Type: application/json" \
         -d "{\"content\":\"**$title**\n$message\"}" \
         "$DISCORD_WEBHOOK"
}

# Check if backup directory is mounted
if ! mountpoint -q /media/sf_letta_backups; then
    notify "Backup Failed" "Error: Backup location not mounted at $(date)"
    exit 1
fi

# Create backup directories if they don't exist
if ! mkdir -p "$BACKUP_DIR"; then
    notify "Backup Failed" "Error: Cannot create backup directory at $(date)"
    exit 1
fi

# Function to create exclude list from .gitignore
create_exclude_list() {
    local temp_excludes=$(mktemp)
    # Start with standard excludes
    cat > "$temp_excludes" << EOF
.git/
*.pyc
__pycache__/
*.pyo
*.pyd
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
./roblox/roblox/
./roblox/roblox/**
./roblox/roblox/lib/**
./roblox/roblox/bin/**
./roblox/roblox/include/**
./roblox/roblox/src/**
./roblox/roblox/lib/python3.10/**
./roblox/roblox/lib/python3.10/site-packages/**
**/__pycache__
.pytest_cache/
.env.example
**/backups/
**/*.cpython-*.pyc
**/*.pytest_cache
api/storage/thumbnails/
api/storage/avatars/
api/storage/assets/thumbnails/
api/letta-roblox-client/
**/*.test.ts
**/*.test.py
tests/
api/tests/
venv/
.venv/
virtualenv/
EOF

    # Add .gitignore contents if it exists
    if [ -f "$REPO_DIR/.gitignore" ]; then
        # Filter out important files from gitignore
        grep -v -E "\.db$|\.env$|\.bak$|storage\/|\.rbxm$|\.lua$|\.json$" "$REPO_DIR/.gitignore" >> "$temp_excludes"
    fi
    echo "$temp_excludes"
}

# Get backup size
get_backup_size() {
    local size=$(du -h "$1" | cut -f1)
    echo "$size"
}

# Test mode flag
DRY_RUN=0
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=1
    echo "Running in test mode - no backup will be created"
fi

# Create backup archive
EXCLUDES=$(create_exclude_list)
echo "Starting backup at $(date)..."

# Get estimated file count
echo "Counting files to backup..."
FILE_COUNT=$(find "$REPO_DIR" -type f \
    ! -path "*/\.git/*" \
    ! -path "*/\.pytest_cache/*" \
    ! -path "*/\.vscode/*" \
    ! -path "*/roblox/lib/*" \
    ! -path "*/roblox/bin/*" \
    ! -path "*/roblox/include/*" \
    ! -path "*/roblox/src/*" \
    ! -path "*/roblox/src/letta-roblox/*" | wc -l)
echo "Found approximately $FILE_COUNT files to backup"
notify "Backup Started" "Starting backup of approximately $FILE_COUNT files..."

if [ $DRY_RUN -eq 1 ]; then
    echo "Files that would be included in backup:"
    echo -e "\n=== Source Files ==="
    cd "$REPO_DIR" && \
    find . -type f \( -name "*.lua" -o -name "*.py" -o -name "*.json" -o -name "*.sh" \) \
        ! -path "*/\.git/*" \
        ! -path "*/\.pytest_cache/*" \
        ! -path "*/\.vscode/*" \
        ! -path "*/roblox/lib/*" \
        ! -path "*/roblox/bin/*" \
        ! -path "*/roblox/include/*" \
        ! -path "*/roblox/src/*" \
        ! -path "*/roblox/src/letta-roblox/*" \
        ! -path "*/letta-roblox/*" \
        ! -path "*/tests/*" \
        ! -path "*/__pycache__/*" \
        -print | sort

    echo -e "\n=== Assets ==="
    find . -type f -name "*.rbxm" \
        ! -path "*/backups/*" \
        ! -path "*/roblox/lib/*" \
        ! -path "*/roblox/src/letta-roblox/*" \
        -print | sort

    echo -e "\n=== Databases ==="
    find . -type f \( -name "*.db" -o -name "schema.sql" \) \
        ! -path "*/backups/*" \
        ! -path "*/roblox/lib/*" \
        ! -path "*/roblox/src/letta-roblox/*" \
        -print | sort

    echo -e "\n=== Config Files ==="
    find . -type f \( -name ".env" -o -name "*.env" -o -name "*.bak" -o -name "*.ini" \) \
        ! -path "*/\.git/*" \
        ! -path "*/\.pytest_cache/*" \
        ! -path "*/\.vscode/*" \
        ! -path "*/roblox/lib/*" \
        ! -path "*/roblox/src/letta-roblox/*" \
        -print | sort

    echo -e "\n=== Documentation ==="
    find . -type f \( -name "*.md" -o -name "*.txt" \) \
        ! -path "*/backups/*" \
        ! -path "*/roblox/lib/*" \
        ! -path "*/roblox/src/letta-roblox/*" \
        -print | sort
    exit 0
fi

if ! tar -czf "$BACKUP_DIR/roblox_backup_$DATE.tar.gz" \
    --verbose \
    --exclude="*/roblox/lib/*" \
    --exclude="*/roblox/bin/*" \
    --exclude="*/roblox/include/*" \
    --exclude="*/roblox/src/letta-roblox/*" \
    --exclude="*/site-packages/*" \
    --exclude="*/python3*/*" \
    --exclude="*/dist-packages/*" \
    --exclude="*/__pycache__/*" \
    --exclude="*/.pytest_cache/*" \
    --exclude="*/.git/*" \
    --exclude="*/venv/*" \
    --exclude="*/.venv/*" \
    --exclude="*/virtualenv/*" \
    -C "$REPO_DIR" . 2>&1 | while read line; do
        echo "$line"
        # Send periodic updates to Discord (every 100 files)
        if [ $((++count % 100)) -eq 0 ]; then
            notify "Backup Progress" "Processed $count files..."
        fi
    done; then
    notify "Backup Failed" "Backup failed at $(date)"
    rm -f "$EXCLUDES"
    exit 1
fi

echo "Backup archive created, calculating size..."
rm -f "$EXCLUDES"

# Get backup size
BACKUP_SIZE=$(get_backup_size "$BACKUP_DIR/roblox_backup_$DATE.tar.gz")
echo "Backup size: $BACKUP_SIZE"

# Keep only last 7 backups
echo "Cleaning up old backups..."
ls -t "$BACKUP_DIR"/roblox_backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm

# Log and notify success
echo "Backup completed at $(date)" >> "$BACKUP_DIR/backup.log"
notify "Backup Success" "Backup completed successfully at $(date)\nBackup size: $BACKUP_SIZE" 