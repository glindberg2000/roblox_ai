
# Database Schema Documentation

## agent_mappings
Maps NPCs to their Letta AI agents for persistent conversations.

```sql
CREATE TABLE agent_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_id INTEGER NOT NULL,
    participant_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_type TEXT NOT NULL DEFAULT 'letta',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (npc_id) REFERENCES npcs(id)
);

CREATE INDEX idx_agent_mapping ON agent_mappings(npc_id, participant_id, agent_type);
```

### Fields
- **npc_id**: References the NPC in our system.
- **participant_id**: Unique identifier for the participant (player or NPC).
- **agent_id**: The Letta agent ID for this conversation.
- **agent_type**: Type of AI agent (default 'letta', future-proofed for other providers).
- **created_at**: When this mapping was created.

---

# Letta AI Integration

## Overview
The Letta AI integration provides NPCs with persistent memory and natural conversation capabilities. 

## Components

### 1. Database Layer
- The `agent_mappings` table maintains NPC-to-Agent relationships.
- Functions in `database.py` handle agent mapping CRUD operations.
- NPC context retrieval combines data from `npcs` and `assets` tables.

### 2. API Layer
- `/letta/v1/chat` endpoint handles all NPC conversations.
- Automatic agent creation and management.
- Context preservation across sessions.

### 3. NPC Context
NPCs provide rich context to Letta agents including:
- **System prompt** (personality).
- **Asset description** (appearance).
- **Abilities**.
- **Display name**.

---

## Usage Example

```python
# Create or retrieve agent mapping
agent_mapping = get_agent_mapping(npc_id=123, participant_id="player_456")
if not agent_mapping:
    # Get NPC context
    npc_context = get_npc_context(npc_id)
    # Create new Letta agent
    agent = letta_client.create_agent(
        npc_type="npc",
        initial_memory={
            "persona": npc_context["system_prompt"],
            "description": npc_context["description"],
            "abilities": npc_context["abilities"]
        }
    )
    # Store mapping
    agent_mapping = create_agent_mapping(
        npc_id=npc_id,
        participant_id=participant_id,
        agent_id=agent["id"]
    )

# Send message to agent
response = letta_client.send_message(agent_mapping.agent_id, message)
```

---

## Testing
See `tests/test_letta_oscar.py` for integration test examples.
