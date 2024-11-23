# NPC Spawn Position Not Persisting Issue

## Problem Description
The spawn position coordinates for NPCs are not being reliably read from and written to the database due to inconsistent field naming and double serialization issues.

## Current Behavior
1. Frontend sends both formats:
```javascript
{
    spawnPosition: {x: 0, y: 5, z: 9},  // Object
    spawn_position: '{"x":0,"y":5,"z":9}'  // Already serialized string
}
```

2. Backend double-serializes:
```python
# This causes double serialization
spawn_position = json.dumps(data.get('spawnPosition', {"x": 0, "y": 5, "z": 0}))
```

## Root Cause

1. Double Serialization:
- Frontend serializes to spawn_position
- Backend serializes spawnPosition again
- Results in nested JSON strings

2. Inconsistent Field Names:
- Frontend uses both spawnPosition and spawn_position
- Backend tries to handle both, causing confusion
- Database expects specific format

## Solution

1. Frontend Changes:
```javascript
// Remove double serialization
const formattedData = {
    ...data
    // No spawn_position field, just use spawnPosition object
};
```

2. Backend Changes:
```python
# Single serialization point
spawn_position = json.dumps(data['spawnPosition'])

cursor.execute("""
    UPDATE npcs 
    SET spawn_position = ?
    WHERE npc_id = ? AND game_id = ?
""", (spawn_position, npc_id, game_id))
```

3. Data Flow:
- Frontend sends: `spawnPosition` as object
- Backend serializes once for storage
- Database stores single JSON string
- Frontend receives and parses once

## Implementation Steps

1. Standardize on `spawnPosition`:
- Frontend sends as object
- Backend serializes once
- Database column remains `spawn_position`
- Frontend receives as object

2. Remove Double Serialization:
- Remove `spawn_position` from frontend data
- Single serialization point in backend
- Single parse point in frontend

3. Consistent Field Names:
- Use `spawnPosition` in code
- Use `spawn_position` only for database column
- Remove redundant conversions

## Verification
1. Frontend sends correct format
2. Backend serializes once
3. Database stores valid JSON
4. Frontend receives parseable data
5. Lua files show correct coordinates

## Success Criteria
1. Spawn position persists between edits
2. No double serialization in logs
3. Clean data flow through system
4. Consistent coordinate display 