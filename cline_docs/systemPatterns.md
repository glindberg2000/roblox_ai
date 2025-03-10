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
- Track member changes
- Use display names for consistency
- Quick updates on departure
- Maintain group context

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
   - Use string format: "key: value | key: value"
   - Update on health changes
   - Update on location changes
   - Update on group changes
   - Should update on spawn (to be implemented)

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

## Location Handling
- Track nearest location
- Use location names for narrative
- Monitor coordinate changes
- Handle location transitions

## Message Handling
- System message cleanup needed
- First interaction needs echo fix
- Coordinate alerts need refinement

## Agent Lifecycle
- Create on spawn
- Verify before updates
- Maintain status consistency

## Message Flow
1. Server generates message (NPC/System)
2. NPCChatHandler processes message
3. NPCChatMessageEvent fired to clients
4. Client should:
   - Display chat bubble (working)
   - Show in TextChatService text box (not working)

## Known Components
1. Server-side:
   - NPCChatHandler
   - InteractionService
   - GroupProcessor
   - Status update system

2. Client-side:
   - NPCChatClient
   - TextChatService integration

## System Message Types
1. Proximity notifications
2. Group membership changes
3. Status updates
4. NPC chat responses

## Chat Display Methods
1. Chat Bubbles:
   - Using ChatService:Chat()
   - Working correctly

2. Text Box:
   - Using TextChatService
   - Not displaying messages
   - Client-side handling needs review

## Action Patterns
- Hunt System
  - Uses NavigationService with combat parameters
  - Supports both player and NPC targets
  - Different hunt types (destroy/track)
  - Continuous target tracking

- Combat Navigation
  - Aggressive pathfinding
  - Jump-enabled pursuit
  - Frequent path updates
  - Close-range direct movement 