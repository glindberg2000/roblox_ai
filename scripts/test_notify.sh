#!/bin/bash
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1324609509280452730/N-jxjPk7XxD8JYoLZmjw65fa_cmT82KT8Tn7IHB4uJ6-4HhIjxhsAfz7Aa6GEAsQp5a_"

curl -H "Content-Type: application/json" \
     -d '{"content":"**Test Notification**\nThis is a test message"}' \
     "$DISCORD_WEBHOOK"
