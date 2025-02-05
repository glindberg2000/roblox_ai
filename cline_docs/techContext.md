# Technical Context

## Core Technologies
- Roblox Studio
- Lua
- HTTP Service (pending for API)

## Key Services
- LoggerService
- NPCManagerV3
- InteractionService
- API Service (planned)

## Development Setup
- Git for version control
- Rojo for file sync
- External API integration planned

## Technical Constraints
- Rate limits for API calls
- Need for retry logic
- Event batching requirements
- Error handling needs

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