#!/bin/bash

# Create private backup directory outside of git repo
mkdir -p ../roblox_private_assets
mkdir -p ../roblox_private_assets/databases
mkdir -p ../roblox_private_assets/assets
mkdir -p ../roblox_private_assets/config

# Backup all database files (including SQLite)
cp src/data/*.{json,lua,db,sqlite,sqlite3} ../roblox_private_assets/databases/

# Backup assets and config
cp -r api/storage/* ../roblox_private_assets/assets/
cp api/.env ../roblox_private_assets/config/ 