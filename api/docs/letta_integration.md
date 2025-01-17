# Letta AI Integration

## Overview
The Letta AI integration provides NPCs with persistent memory and natural conversation capabilities. 

## Components

### 1. Database Layer
- `agent_mappings` table maintains NPC-to-Agent relationships
- Functions in `database.py` handle agent mapping CRUD operations
- NPC context retrieval combines data from npcs and assets tables

### 2. API Layer
- `/letta/v1/chat` endpoint handles all NPC conversations
- Automatic agent creation and management
- Context preservation across sessions

### 3. NPC Context
NPCs provide rich context to Letta agents including:
- System prompt (personality)
- Asset description (appearance)
- Abilities
- Display name

## Usage Example 