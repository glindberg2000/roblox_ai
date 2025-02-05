# Technical Context

## Status Update System
```lua
-- Format: key: value | key: value
status_text = "health: 100 | location: Cafe | current_action: Idle"
```

## Group Update Format
```lua
-- Should use display names
members = {
    [displayName] = {
        name = displayName,
        appearance = description,
        last_seen = timestamp
    }
}
```

## Location System
```lua
-- Current format
location = location_slug

-- Should be
location = location_name
```

## Known Technical Issues
1. Group updates using wrong identifier (playerid vs displayName)
2. Missing spawn initialization for status updates
3. Echo in first interaction with NPCs
4. Slow group departure updates
5. System message accumulation
6. Coordinate system alerts need refinement

## Core Technologies
- Roblox Studio
- Lua
- HTTP Service for API integration
- TextChatService for messaging

## Key Services
- LoggerService: Centralized logging
- NPCManagerV3: NPC state management
- InteractionService: Proximity and clusters
- LettaConfig: API configuration

## Development Setup
- Git for version control
- Rojo for file sync
- External API integration
- Debug logging enabled

## Technical Constraints
1. API Integration
   - Rate limits for API calls
   - Need for retry logic
   - Error handling for failed calls

2. Chat System
   - TextChatService limitations
   - System message handling
   - Echo prevention needed

3. State Management
   - Agent creation verification
   - Status update timing
   - Group state consistency

4. Performance
   - Message batching
   - Update throttling
   - Resource monitoring

## Chat System Components
1. TextChatService
   - CreateMessage() for message creation
   - SendTextMessage() for chat window display
   - System message integration

2. Chat Service
   - Bubble creation and display
   - Character-based chat visualization

3. Custom Events
   - NPCChatMessageEvent for server-client communication
   - MessageReceived for chat monitoring

## Development Setup
- Roblox Studio
- TextChatService enabled
- Legacy chat system disabled
- Custom NPC chat implementation

## Technical Constraints
- TextChatService limitations with system messages
- Need to handle both bubble and window chat
- System message ping configuration required

## Technologies Used
1. Roblox Studio
   - Lua scripting
   - Built-in services
   - WebSocket support

2. Backend Services
   - REST API endpoints
   - WebSocket servers
   - State management

3. Tools & Libraries
   - LoggerService
   - JsonEncode/Decode
   - WebSocketService

## Development Setup
1. Required Services
   - HttpService
   - ReplicatedStorage
   - ServerStorage
   - WebSocketService

2. Configuration
   - Enable HTTP requests
   - Configure API endpoints
   - Set up WebSocket connections

## Technical Constraints
1. Roblox Limitations
   - Server-side WebSocket only
   - Rate limits on API calls
   - Performance considerations

2. System Requirements
   - Regular state updates
   - Real-time interaction
   - Scalable group support 

### Future WebSocket Requirements
1. **Infrastructure**:
   - NGINX reverse proxy with SSL
   - Dynamic DNS configuration
   - Port 443 forwarding
   
2. **Roblox-Specific**:
   - WebSocketService wrapper class
   - Fallback to HTTP when WS disconnected
   - Message compression (BSON/MessagePack)

3. **Monitoring**:
   - Connection health checks
   - WS-specific rate limiting
   - DDOS protection 

### Updated Team Structure
1. **Roles**:
   - RD: Roblox Core Systems
   - LD: Letta Integration & AI Services
   - HD: Testing & Coordination
2. **Testing Strategy**:
   - LD Lab: Unit tests for Letta components
   - RD Sandbox: Cluster simulations
   - HD Load Tests: 50+ NPC scenarios 