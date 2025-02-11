# Active Development Context

## Current Task
Adding NPC animations and actions (jump, sit)

## Recent Changes
1. Fixed chat system
   - Fixed message routing loop
   - Added conditional heartbeat reminder
   - Improved system message handling
   - Fixed TextChatService integration

## Current State
### Working
- Chat system fully functional
- Message routing fixed
- System message handling improved
- TextChatService integration complete

### Next Implementation
- Jump action and animation
- Sit state tracking
- Status updates for animations
- Prompt updates for actions

## Implementation Plan
1. Animation System
   - Add jump animation
   - Track sitting state
   - Update status system

2. Action Commands
   - Implement jump command
   - Add sit state handling
   - Update prompt for actions

3. Status Updates
   - Track animation states
   - Add sitting status
   - Update status format

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