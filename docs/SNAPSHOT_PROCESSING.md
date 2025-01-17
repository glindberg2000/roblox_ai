# Snapshot Processing Investigation

## Current Status (2024-01-14)

### Fixed & Verified
- Backend error resolved by correcting GroupData model usage
- Position data successfully flowing through to ADE
- Full position tracking confirmed working:
  ```json
  {
    "current_location": "8.113263130187988, 19.85175323486328, -12.013647079467773",
    "current_action": "idle",
    "movement_state": "stationary",
    "previous_location": "8.113263130187988, 19.85175323486328, -12.013647079467773"
  }
  ```

### Current Working State
- Complete position tracking pipeline working:
  1. Lua client captures positions
  2. Backend processes and validates data
  3. ADE receives and tracks positions
- Group membership tracking working
- All data properly validated through Pydantic models

### Sample Working Data
```python
# Example of correctly processed data
currentGroups=GroupData(
    members=['Kaiden', 'Goldie', 'Noobster', 'Diamond'], 
    npcs=4, 
    players=0, 
    formed=1736840734
)
position=PositionData(
    x=8.113263130187988, 
    y=19.85175323486328, 
    z=-12.013647079467773
)
```

### Relevant Files for Next Session
- api/app/letta_router.py
- api/app/models.py
- games/sandbox-v2/src/shared/NPCSystem/services/GameStateService.lua

### Key Log Evidence
```
[DEBUG] [SNAPSHOT] Response: {
  "StatusMessage": "Internal Server Error",
  "Success": false,
  "StatusCode": 500,
  "Body": "{\"detail\":\"Internal server error\",\"error\":\"'dict' object has no attribute 'members'\"}"
}
```

### Raw Context Sample
```json
{
  "relationships": [],
  "currentGroups": {
    "members": ["Kaiden", "Goldie", "Noobster", "Diamond"],
    "npcs": 4,
    "players": 0,
    "formed": 1736840137
  },
  "position": {
    "y": 19.85175132751465,
    "x": 12.096878051757813,
    "z": -11.488070487976075
  },
  "location": "Unknown",
  "recentInteractions": []
}
```

## Next Steps
1. Debug snapshot processing in letta_router.py
2. Verify cluster data structure handling
3. Add additional error logging around dict access 