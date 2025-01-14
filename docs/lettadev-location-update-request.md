# Location Update Implementation Question

## Current Status

1. **Successfully Getting Positions in Lua**
   ```lua
   -- In GameStateService.lua
   if success then
       positionData = {
           x = position.X,
           y = position.Y,
           z = position.Z
       }
       location = "Unknown"  -- Named location can be added later
   end
   ```

2. **Sending in Snapshot**
   ```json
   {
       "humanContext": {
           "NPCName": {
               "position": {
                   "x": 12.1,
                   "y": 19.9,
                   "z": -11.5
               }
           }
       }
   }
   ```

3. **Current Memory Blocks**
   ```json
   "status": {
       "current_location": "Unknown",
       "current_action": "idle",
       "movement_state": "stationary",
       "previous_location": "Unknown"
   }
   ```

## Questions

1. How should coordinates be stored in memory blocks?
   - Add to status block as coordinates field?
   - Add to group_members block for each member?
   - Use a separate position/location block?

2. What's the recommended format for coordinates?
   ```python
   # Option 1: List format
   "coordinates": [12.1, 19.9, -11.5]
   
   # Option 2: Object format
   "coordinates": {"x": 12.1, "y": 19.9, "z": -11.5}
   
   # Option 3: String format
   "current_location": "12.1, 19.9, -11.5"
   ```

3. Should we track both named locations and raw coordinates?
   ```json
   {
       "current_location": "Calvin's Calzone",  // Named location
       "coordinates": [12.1, 19.9, -11.5]      // Raw position
   }
   ```

4. Should coordinates be included in group member data?
   ```json
   "members": {
       "Kaiden": {
           "name": "Kaiden",
           "coordinates": [12.1, 19.9, -11.5],
           "appearance": "",
           "notes": ""
       }
   }
   ```

Thank you! 