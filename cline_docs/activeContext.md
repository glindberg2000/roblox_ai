# Active Development Context

## Current Task
- Adding hunt action for NPCs to target players and other NPCs

## Recent Changes
1. Added hunt action system
   - Implemented CombatNavigate in NavigationService
   - Added hunt action to ActionService
   - Support for both player and NPC targets
   - Different hunt types (destroy/track)

2. Combat Navigation Parameters
   - Aggressive pathfinding for destroy mode
   - Continuous target tracking
   - Optimized update intervals
   - Jump-enabled pursuit

## Current State
### Working
- Basic hunt command structure
- Combat navigation pathfinding
- Target type detection (Player/NPC)
- Hunt type differentiation

### Next Implementation
- Test hunt behaviors
- Add combat animations
- Implement attack range
- Add cooldown system

## Implementation Plan
1. Combat System
   - Test hunt command flow
   - Verify target acquisition
   - Check pathfinding behavior
   - Add combat animations

2. Hunt Types
   - Destroy: Aggressive pursuit
   - Track: Casual following
   - Add more behaviors later

3. Status Updates
   - Track combat state
   - Show current target
   - Update hunt status

## Technical Requirements
1. Animation
   ```lua
   -- Animation format
   local jumpAnim = Instance.new("Animation")
   jumpAnim.AnimationId = "rbxassetid://507765644"
   ```

2. Status Format
   ```lua
   -- New status format
   status = "health: 100 | location: Cafe | state: sitting"
   ```

3. Action Commands
   ```lua
   -- New action structure
   action = {
       type = "jump",
       data = {
           height = 5,
           animation = jumpAnim
       }
   }
   ```

## Current Task Context

## Issue: System Messages and Chat Display
Currently investigating two related issues:
1. System messages being triggered from multiple places
2. Chat messages only showing in bubbles, not in TextChatService text box

### Known Message Sources
1. InteractionService - Player proximity/range notifications
2. GroupProcessor - Group membership changes
3. Status updates (notifications disabled)
4. Chat system - NPC responses

### Chat Display Status
- ✅ Chat bubbles working
- ❌ TextChatService text box not showing messages
- ✅ Server sending messages via NPCChatMessageEvent
- ❌ Client handling of TextChatService needs review

### Next Steps
1. Track down all system message triggers:
   - Review InteractionService
   - Review GroupProcessor
   - Check for other potential sources
2. Fix TextChatService integration:
   - Review client-side chat handling
   - Verify TextChatService configuration
   - Debug message routing to text box

### Current Progress
- Disabled notifications for status updates
- Confirmed group updates don't send notifications by default
- Need to investigate system message triggers
- Need to fix TextChatService integration 