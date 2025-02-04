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