#!/bin/bash

# Activate virtual environment
source roblox/bin/activate

# Save only direct dependencies (no sub-dependencies)
pip freeze > api/requirements.txt.temp
cat api/requirements.txt.temp | grep -v "^#" | grep -v "^-e" > api/requirements.txt
rm api/requirements.txt.temp 