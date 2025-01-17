# Status Block Update Issue

## Current Behavior

1. We're updating the status block with coordinates:
```python
status = get_memory_block(direct_client, agent_id, "status")
new_status = status.copy()
new_status["coordinates"] = coordinates
update_memory_block(direct_client, agent_id, "status", new_status)
```

2. But the memory block shows no coordinates:
```json
"status": {
    "current_location": "Unknown",
    "current_action": "idle",
    "movement_state": "stationary",
    "previous_location": "Unknown"
}
```

## Questions

1. Are updates to memory blocks working correctly? 
2. Is there a schema validation that might be removing the coordinates?
3. Could you test updating a status block on your end?
4. Should we modify the status block schema to include coordinates?

## Debug Info
- We're using `update_memory_block()` from letta_templates.npc_utils
- The coordinates are in the correct format from Lua
- The status block seems to reset to default values

Thank you! 