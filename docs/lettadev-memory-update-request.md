# Memory Block Update Implementation Request

## Current Implementation Status

### Working Components
1. **Group State Tracking**
   ```python
   # Successfully grouping NPCs by cluster
   cluster_groups = {
       group_key: {
           'members': set(context.currentGroups.members),
           'agent_ids': []
       }
   }
   ```

2. **Memory Block Retrieval**
   ```python
   # Successfully getting current state
   current = get_memory_block(direct_client, agent_id, "group_members")
   ```

3. **State Change Detection**
   ```python
   # Successfully tracking changes
   old_members = set(current.get("members", {}).keys())
   new_members = set(canonical_members.keys())
   ```

### Current Error
```
Failed to update agent agent-dfa21ed2-51aa-4785-9c03-88aba0122d2a: name 'update_memory_block' is not defined
```

## Questions for LettaDev

1. **Memory Block Updates**
   - What is the correct method to update memory blocks?
   - Should we be using a different API call?
   - Is there a specific client method instead of `update_memory_block`?

2. **Current Update Attempt**
   ```python
   # Our current approach
   current["members"] = canonical_members
   current["last_updated"] = datetime.now().isoformat()
   current["summary"] = f"Current members: {', '.join(canonical_members.keys())}"
   
   # This fails:
   update_memory_block(direct_client, agent_id, "group_members", current)
   ```

3. **Context**
   - We're updating group membership as clusters change
   - Need to maintain consistent state across all NPCs in cluster
   - Want to track join/leave events in updates list

## Implementation Goals
1. Atomic updates to prevent state conflicts
2. Maintain update history
3. Keep all NPCs in cluster synchronized
4. Track member changes properly

## Current Log Output
```
roblox_app - INFO - Processing cluster with members: ['Noobster', 'Kaiden', 'Diamond', 'Goldie']
roblox_app - ERROR - Failed to update agent agent-dfa21ed2-51aa-4785-9c03-88aba0122d2a: name 'update_memory_block' is not defined
roblox_app - ERROR - Failed to update agent agent-6051a002-ab41-4fda-af0c-ce61b6f0dabe: name 'update_memory_block' is not defined
```

Could you please provide:
1. The correct method/API for updating memory blocks
2. Any best practices for maintaining group state
3. Recommended patterns for tracking state changes

Thank you! 