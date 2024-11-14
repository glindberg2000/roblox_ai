#!/bin/bash

# Restore all database files (including SQLite)
cp ../roblox_private_assets/databases/*.{json,lua,db,sqlite,sqlite3} src/data/

# Restore assets and config
cp -r ../roblox_private_assets/assets/* api/storage/
cp ../roblox_private_assets/config/.env api/ 