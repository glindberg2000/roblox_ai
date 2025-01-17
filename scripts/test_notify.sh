#!/bin/bash
DISCORD_WEBHOOK="***REMOVED***"

curl -H "Content-Type: application/json" \
     -d '{"content":"**Test Notification**\nThis is a test message"}' \
     "$DISCORD_WEBHOOK"
