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
1. NPCManagerV3
   - Central management of NPCs
   - Parallel message processing
   - Thread-per-message pattern
   - Built-in deduplication (1s window)

2. InteractionService
   - Proximity-only checks
   - No conversation locking
   - Cluster-based validation

3. Message Processing
   - Immediate parallel processing
   - Thread spawning per message
   - No artificial delays
   - Natural AI response timing

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