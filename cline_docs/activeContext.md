# Active Development Context

## Current Task
Improving NPC status and group updates

## Recent Changes
- Simplified status updates to use string format
- Fixed message routing from player to NPC
- Implemented cluster-based group detection
- Added health and location tracking

## Current State
### Working
- Player -> NPC message routing
- Cluster detection and formation
- Health and location tracking
- Basic group detection
- Status updates (new string format)
- Basic chat functionality
- Core interaction logic
- State tracking and conversation management

### Known Issues
1. Group Updates
   - Using playerid instead of display name
   - Slow updates on group departure
   - Need to verify member format

2. Status Updates
   - Need location names instead of slugs
   - Missing spawn initialization
   - Could improve narrative style

3. Interaction Issues
   - Echo on first interaction
   - System message cleanup needed
   - Coordinate alerts need refinement

4. Message Broadcasting
   - Only closest NPC receives messages
   - NPC-NPC chat commented out (but functional)
   - Need to implement group broadcasting

## Next Steps
1. Fix group member format (use display names)
2. Add spawn status initialization
3. Implement message broadcasting
4. Fix first interaction echo
5. Clean up system messages
6. Speed up group departure updates
7. Improve status narrative style

## Implementation Plan
1. Group Updates
   - Switch to display names
   - Speed up departure detection
   - Add broadcast support

2. Status Updates
   - Add spawn initialization
   - Use location names
   - Improve narrative format

3. Message Handling
   - Fix echo issue
   - Add broadcasting
   - Clean up system messages

## Testing Status
- Health system verified working
- Location system verified working
- Message routing verified working
- Cluster system functioning
- API integration complete

# Current Task Context

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