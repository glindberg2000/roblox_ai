# Current Letta Templates Implementation

## Overview
We're currently using letta_templates for tool definitions, registration, and system instructions in our NPC system.

## Latest Version (v0.7.0-roblox-1)

### Installation
```bash
pip install git+https://github.com/glindberg2000/letta-templates@v0.7.0-roblox-1
```

### New Integration Method
```python
from letta_templates.roblox_integration import RobloxNPCManager

# Create manager instance
npc_manager = RobloxNPCManager(letta_client)

# Create memory blocks for NPC
memory_blocks = npc_manager.create_memory_blocks(
    npc_name="Diamond",
    npc_description="A friendly NPC guide",
    location_data={...},
    group_data={...}
)

# Update group status
npc_manager.update_group_status(
    agent_id="agent_123",
    group_members=["Alice", "Bob"],
    location="Main Plaza"
)
```

## Current Implementation

### Tool Imports
```python
from letta_templates.npc_tools import (
    TOOL_INSTRUCTIONS,
    TOOL_REGISTRY,
    navigate_to,
    navigate_to_coordinates,
    perform_action,
    examine_object
)
```

### Agent Creation
```python
def create_roblox_agent(
    client, 
    name: str,
    memory: ChatMemory,
    system: str,
    embedding_config: Optional[EmbeddingConfig] = None,
    llm_type: str = None,
    tools_section: str = TOOL_INSTRUCTIONS
):
    """Create a Letta agent configured for Roblox NPCs"""
    
    # Add tools section to system prompt
    system_prompt = system.replace(
        "Base instructions finished.",
        TOOL_INSTRUCTIONS + "\nBase instructions finished."
    )

    # Get tool IDs
    tool_ids = register_base_tools(client)
    
    return client.create_agent(
        name=name,
        embedding_config=embedding_config,
        llm_config=llm_config,
        memory=memory,
        system=system_prompt,
        include_base_tools=True,
        tool_ids=tool_ids,
        description="A Roblox NPC"
    )
```

### Tool Registration
```python
def register_base_tools(client) -> List[str]:
    """Register base tools for all agents and return tool IDs"""
    existing_tools = {tool.name: tool.id for tool in client.list_tools()}
    
    tool_ids = []
    for name, info in TOOL_REGISTRY.items():
        if name in existing_tools:
            tool_ids.append(existing_tools[name])
        else:
            tool = client.create_tool(info["function"], name=name)
            tool_ids.append(tool.id)
    
    return tool_ids
```

## Currently Used Tools
1. navigate_to: Move NPC to location
2. navigate_to_coordinates: Move NPC to specific coordinates
3. perform_action: Execute NPC actions
4. examine_object: Inspect game objects

## Integration Points
1. Agent Creation: Tools added during agent initialization
2. System Prompt: Tool instructions injected into prompt
3. Tool Processing: Results handled in process_tool_results()

## Questions for LettaDev
1. Are there new tools in the latest version we should integrate?
2. Should we update our tool registration process?
3. Are we using the latest version of TOOL_INSTRUCTIONS?
4. How should we handle the new memory tools?
5. Should we migrate to using RobloxNPCManager for all NPC operations?
6. What's the best way to transition from our current tool registration to the new system?

## Next Steps
1. Review latest letta_templates version
2. Update tool definitions if needed
3. Integrate any new memory management tools
4. Update system prompts for new capabilities
5. Test RobloxNPCManager integration
6. Plan migration strategy from current system 

## Proposed Wrapper Configuration

### Core NPC Configuration
```python
npc_config = {
    "id": "88f731d0-593b-4443-9ced-430e78387e0b",  # NPC's UUID
    "name": "Diamond",                              # Display name
    "description": "A friendly NPC guide",          # Base personality
    "abilities": ["chat", "move", "emote"],        # Available actions
    "llm_type": "gpt-4-0125-preview"               # Model preference
}
```

### Memory Configuration
```python
memory_config = {
    "blocks": {
        "group_members": {
            "limit": 5000,          # Memory block size
            "ttl": 3600,           # Time to live for entries
            "summarize": True      # Auto-summarize old entries
        },
        "locations": {
            "limit": 2000,
            "include_coordinates": True
        }
    },
    "archival": {
        "enabled": True,
        "db_connection": "sqlite:///game_data.db"
    }
}
```

### Status Configuration
```python
status_config = {
    "update_interval": 5,           # How often to sync status
    "proximity_radius": 10,         # Distance for group formation
    "location_tracking": True,      # Track position changes
    "group_tracking": True          # Track group membership
}
```

### Example Usage
```python
from letta_templates.roblox_integration import RobloxNPCManager

# Initialize manager with configs
npc_manager = RobloxNPCManager(
    letta_client=client,
    npc_config=npc_config,
    memory_config=memory_config,
    status_config=status_config
)

# Get a fully configured agent
agent = npc_manager.create_agent()

# Update group status (automatically handles memory/archival)
npc_manager.update_group_status(
    agent_id=agent.id,
    group_members=["Alice", "Bob"],
    location="Main Plaza"
) 