# Active Development Context

## Current Task
Implementing NPC chat system with both chat bubbles and chatbox integration

## Recent Changes
- Successfully implemented chat bubbles appearing above NPC heads
- Successfully sending messages through TextChatService using CreateMessage and SendTextMessage
- Disabled system message pings temporarily
- Chat messages appear in both bubbles and chat window

## Current Issues
- Need to re-enable status and group update blocks
- System message pings are currently disabled

## Next Steps
1. Re-enable status and group update blocks
2. Review system message ping functionality
3. Test chat system with multiple NPCs and players
4. Document chat system architecture

## Current State (Critical Issues)

## System Status: BROKEN
- No user messages are being created or routed
- Only system messages and their responses are displayed
- No player messages reach NPCs
- No messages route back to groups
- Cluster system partially implemented but breaking core functionality

## Core Issues
1. Message Routing Broken
   - Player -> NPC routing not working
   - NPC -> Group routing not working
   - Basic chat functionality non-functional

2. Cluster System Problems
   - Partially implemented
   - Breaking core interaction logic
   - Missing constants (CLUSTER_UPDATE_INTERVAL)

3. Conversation Management
   - Locks not working properly
   - State tracking unreliable
   - Multiple conversations possible when shouldn't be

## Critical Files Affected
- NPCManagerV3.lua
- InteractionService.lua
- GameStateService.lua

## Current Focus
   - Test multi-user interactions
   - Monitor system performance
   - Document thread usage patterns

### Current Focus
**Active Tickets**:
1. CLUSTER-01 (RD): Snapshot migration
2. TEST-05 (HD): Load test setup

**Blockers**:
- Awaiting Letta batch API docs (LD) 