# Technical Context: NPC System

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