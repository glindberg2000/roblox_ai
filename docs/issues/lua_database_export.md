# Lua Database Export Format Issue

## Problem Description
The current Lua database export functionality doesn't generate the correct format for NPC and Asset databases. The output format doesn't match the required structure used by the Roblox game.

### Current Output Format
```lua
return {
    npcs = {
        {
            id = "npc_id",
            displayName = "name",
            assetId = "asset_id",
            systemPrompt = "prompt",
            responseRadius = 20,
            spawnPosition = {x = 0, y = 5, z = 0},
            abilities = ["ability1", "ability2"]
        }
    }
}
```

### Required Format
```lua
return {
    npcs = {
        {
            id = "4e5f05a7-028e-40cc-93fe-c24bb22042d7",
            displayName = "Pete",
            name = "Pete",
            assetId = "7315192066",
            model = "7315192066",
            modelName = "Pete",
            system_prompt = "...", 
            responseRadius = 20,
            spawnPosition = Vector3.new(-12.389, 17.906, -127.139),
            abilities = {
                "follow",
                "unfollow",
                "inspect",
            },
            shortTermMemory = {}
        }
    }
}
```

## Code Analysis

### Redundant Code
1. Lua generation exists in both:
   - database.py: generate_lua_from_db()
   - utils.py: save_lua_database()

2. Unused utility functions:
   - load_json_database() - No longer needed with SQLite
   - save_json_database() - No longer needed with SQLite

### Current Implementation Issues
1. Vector3 formatting:
   ```python
   json.loads(npc.get("spawn_position", "{}"))  # Wrong
   # Should be:
   f"Vector3.new({pos['x']}, {pos['y']}, {pos['z']})"  # Correct
   ```

2. Missing fields:
   - model
   - modelName 
   - shortTermMemory
   - name (same as displayName)

3. Incorrect field names:
   - systemPrompt vs system_prompt

## Proposed Solution

1. Consolidate Lua generation:
   - Move all Lua generation to utils.py
   - Remove redundant functions from database.py
   - Create dedicated formatters for NPCs and Assets

2. Update format functions:
   - Add proper Vector3 formatting
   - Include all required fields
   - Use correct field names
   - Add shortTermMemory initialization

3. Update database queries:
   - Filter by game slug
   - Include all required fields
   - Join with assets table for additional data

## Questions/Concerns

1. Data Consistency:
   - Should modelName always match displayName?
   - Are abilities always those three default ones?
   - Should shortTermMemory be configurable?

2. Database Schema:
   - Do we need to add model_name field?
   - Should we store Vector3 components separately?

3. Migration:
   - How to handle existing data?
   - Should we update all game instances?

## Next Steps

1. Create new formatting functions in utils.py
2. Update database queries
3. Remove redundant code
4. Add validation for required fields
5. Update tests if they exist
6. Create migration script for existing data

## Required Changes

1. utils.py:
   - Add format_npc_lua()
   - Add format_vector3_lua()
   - Remove unused JSON functions

2. database.py:
   - Update generate_lua_from_db()
   - Add game slug filtering
   - Remove redundant functions

3. dashboard_router.py:
   - Update routes to use new functions
   - Add validation for required fields 