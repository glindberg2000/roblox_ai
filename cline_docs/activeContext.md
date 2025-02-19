# Active Development Context

## Current Task
Investigating chat system error and status update efficiency:

1. Chat Error:
```
ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient:148: attempt to call a nil value
```
- Error occurs in handleLettaChat function
- Affects chat message processing
- May be related to processResponse being nil

2. Status Update Investigation
- Status updates not triggering for all actions (hunt, patrol)
- Need to evaluate whether status updates should happen in API vs game
- Current round-trip to game server may be inefficient

3. Group Member Updates
- Appearance fields not being updated when members join clusters
- Need to investigate upsert_group_member implementation
- May need to restore lost functionality for appearance updates

## Recent Changes
1. Added hunt behavior priority
   - Made HUNT an exclusive behavior
   - Set high priority (90) below EMERGENCY (100)
   - Keeps existing KillBotService implementation

## Current State
### Working
- Basic hunt command structure with proper priority
- Combat navigation pathfinding
- Target type detection (Player/NPC)
- Hunt type differentiation

### Issues to Address
1. Chat System
   - Fix nil value error in V4ChatClient
   - Review chat message processing flow

2. Status Updates
   - Evaluate API vs game server updates
   - Add missing action status updates
   - Consider more efficient update patterns

3. Group Updates
   - Investigate appearance field updates
   - Review upsert_group_member functionality
   - Consider API-side group member updates

## Next Steps
1. Debug V4ChatClient error
   - Trace processResponse initialization
   - Add nil checks where needed
   - Review chat message flow

2. Status Update Optimization
   - Review current update patterns
   - Consider moving updates to API side
   - Add missing action status triggers

3. Group Member Updates
   - Review appearance update flow
   - Investigate lost functionality
   - Consider API-side member updates

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