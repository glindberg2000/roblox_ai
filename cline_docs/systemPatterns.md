# System Architecture & Patterns

## Chat System Architecture
1. Server-side (NPCChatHandler)
   - Handles chat message processing
   - Manages NPC responses
   - Sends messages via NPCChatMessageEvent

2. Client-side (NPCChatClient)
   - Receives messages via NPCChatMessageEvent
   - Creates chat bubbles
   - Integrates with TextChatService
   - Formats and displays messages in chat window

## Key Technical Decisions
- Using TextChatService for chat window integration
- Separate bubble and window chat display
- System messages for NPC communication
- Event-based communication between server and client

## Current Patterns
- Event-driven messaging
- Centralized chat handling
- Dual display system (bubbles + chatbox)

## Core Components
1. Game Services
   - GameStateService: Manages state sync (2s local, 10s backend)
   - InteractionService: Handles proximity and clusters
   - LoggerService: Centralized logging

2. API Services
   - Snapshot Processing: Enriches game state data
   - Chat Processing: Handles NPC conversations
   - Queue System: Manages message processing

## Key Patterns
1. State Management
   - Regular snapshots for game state
   - Real-time updates for critical changes
   - Memory blocks for NPC context

2. Interaction Patterns
   - Proximity-based clustering
   - Group conversation handling
   - Message queue processing

3. Data Flow
   - Game -> API -> LLM -> Response
   - State updates through snapshot system
   - Context enrichment via processor

## Current Focus
- Optimizing group update flow
- Leveraging existing snapshot processor
- Improving state synchronization

## Future Considerations
1. Thread Management
   - Consider thread pool limits
   - Queue messages when pool is full
   - Monitor thread usage

2. Performance Patterns
   - Track thread creation/cleanup
   - Monitor memory usage
   - Implement graceful degradation

## Key Patterns
1. Event-Driven Architecture
   - System messages trigger interactions
   - Proximity events drive state changes
   - Message-based communication

2. State Management
   - Regular snapshots
   - Immediate critical updates
   - Cluster-based state tracking

3. Service Pattern
   - Separated concerns
   - Clear interfaces
   - Modular design

## NPC Identification
- NPCs have multiple identifiers:
  - npc.id: Used for internal game references
  - npc.displayName: Used for display and some API calls
  - No AgentId in game code - handled by API

## API Integration Patterns
- Game sends what it has (displayName, id)
- API handles mapping to Letta agent IDs
- Consistent with other endpoints (chat, snapshot)

## Group Management
- Attempted pattern:
  1. Detect cluster changes
  2. Send group updates to API
  3. API updates Letta agent memory
- Current blocker: NPC ID access in proximity code

## State Management
- Central NPC manager (npcManagerV3)
- State tracking via lastKnownLocations and lastKnownHealth
- Event-based state change detection

## Health System
- Uses Humanoid.Health for state
- TakeDamage() for health reduction
- Direct Health setting for healing
- Percentage-based health tracking

## Location System
- Known locations list with coordinates
- Radius-based location detection
- Slug-based location tracking
- Change detection via state comparison

## Logging System
- Centralized LoggerService
- Debug/Info/Error levels
- Structured logging format

## API Integration Pattern
1. Status Updates
   - Location changes trigger update
   - Health changes trigger update
   - Updates batched when possible
   - Critical changes sent immediately

2. Data Flow
   - Game detects state change
   - APIService formats update
   - API updates status block
   - LLM uses in conversations

3. Rate Limiting Pattern
   - Batch similar updates
   - Minimum time between updates
   - Priority queue for critical changes

## State Change Detection
- Location: Compare against lastKnownLocations
- Health: Compare against lastKnownHealth
- Immediate notification of critical changes
- Batched updates for minor changes

## Error Handling Pattern
1. Failed Calls
   - Retry with backoff
   - Queue during outages
   - Log all failures

2. Data Validation
   - Verify before sending
   - Handle API errors
   - Log invalid states

## Status Update Pattern
1. Data Structure
   ```python
   status_data = {
       "location": str,
       "health": {
           "state": str,  # Dead/Critical/Injured/Healthy
           "percentage": int
       },
       "action": str,
       "last_updated": datetime
   }
   ```

2. Update Flow
   - Game detects state change
   - Formats status data dict
   - Sends to /npc/status/update
   - API updates Letta memory

3. Health States
   - Dead: health <= 0
   - Critical: health <= 25
   - Injured: health <= 75
   - Healthy: health > 75

## Integration Patterns
1. Status Updates
   - Use structured dict format
   - Include timestamps
   - Preserve existing fields
   - Support custom fields

2. Rate Limiting
   - Batch similar updates
   - Prioritize critical changes
   - Minimum update interval

3. Error Handling
   - Retry with backoff
   - Queue during outages
   - Log all failures 