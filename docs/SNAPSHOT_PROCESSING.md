# Snapshot Processing Investigation

## Current Status (2024-01-14)

### System Architecture Overview
- Snapshot system runs on a heartbeat loop in GameStateService
- Data collection intervals:
  - Local state: Every 2 seconds
  - API sync: Every 10 seconds
- Concurrency control: Max 1 concurrent sync

### Data Flow
1. **Collection Phase**
   ```lua
   -- GameStateService collects:
   gameState = {
       clusters = {},      -- NPC/Player proximity groups
       events = {},        -- Interaction events
       humanContext = {},  -- Detailed entity states
       lastUpdate = 0,
       lastApiSync = 0
   }
   ```

2. **Processing Phase**
   - Positions and states gathered for all entities
   - Clusters computed based on proximity (10 stud threshold)
   - Movement validation against threshold (0.1 studs)

3. **Sync Phase**
   ```lua
   -- Payload structure
   payload = {
       timestamp = os.time(),
       clusters = npcClusters,
       events = gameState.events,
       humanContext = gameState.humanContext
   }
   ```

### Working Components
- Complete position tracking pipeline:
  1. Lua client captures positions
  2. Backend processes and validates data
  3. ADE receives and tracks positions
- Group membership tracking
- Data validation through Pydantic models

### Sample Working Data
```python
# Example of correctly processed data
currentGroups=GroupData(
    members=['Kaiden', 'Goldie', 'Noobster', 'Diamond'], 
    npcs=4, 
    players=0, 
    formed=1736840734
)
position=PositionData(
    x=8.113263130187988, 
    y=19.85175323486328, 
    z=-12.013647079467773
)
```

### Identified System Components
1. **Data Collection (InteractionService)**
   - Builds proximity matrix
   - Forms clusters of nearby entities
   - Tracks both NPCs and Players

2. **State Management (GameStateService)**
   - Maintains cached state
   - Handles update intervals
   - Manages sync operations

3. **API Integration**
   - Endpoint: https://roblox.ella-ai-care.com/letta/v1/snapshot/game
   - Handles payload serialization and transmission

### Performance Considerations
- Thread management for sync operations
- Cached state to reduce computation
- Throttled updates via intervals
- Movement threshold filtering

### Next Steps
1. Debug snapshot processing in letta_router.py
2. Verify cluster data structure handling
3. Add additional error logging around dict access
4. Consider improvements:
   - Implement parallel data collection
   - Add data compression
   - Implement retry logic
   - Add snapshot queuing
   - Enhance cluster analysis

### Relevant Files
- api/app/letta_router.py
- api/app/models.py
- games/sandbox-v2/src/shared/NPCSystem/services/GameStateService.lua
- games/sandbox-v2/src/shared/NPCSystem/services/InteractionService.lua

### Key Log Evidence
```
[DEBUG] [SNAPSHOT] Response: {
  "StatusMessage": "Internal Server Error",
  "Success": false,
  "StatusCode": 500,
  "Body": "{\"detail\":\"Internal server error\",\"error\":\"'dict' object has no attribute 'members'\"}"
}
```

### Raw Context Sample
```json
{
  "relationships": [],
  "currentGroups": {
    "members": ["Kaiden", "Goldie", "Noobster", "Diamond"],
    "npcs": 4,
    "players": 0,
    "formed": 1736840137
  },
  "position": {
    "y": 19.85175132751465,
    "x": 12.096878051757813,
    "z": -11.488070487976075
  },
  "location": "Unknown",
  "recentInteractions": []
}
```

### Data Collection Details
1. **Position Sources**
   ```lua
   -- In InteractionService:logProximityMatrix
   -- Positions are collected for ALL entities in clusters:
   for _, npc in pairs(npcs) do
       if npc.model and npc.model.PrimaryPart then
           positions[npc.displayName] = {
               x = pos.X,
               y = pos.Y,
               z = pos.Z,
               type = "npc"
           }
       end
   end
   ```

2. **Current Issue**
   ```json
   {
     "currentGroups": {
       "members": ["Kaiden", "Goldie", "Noobster", "Diamond"],
       "npcs": 4,
       "players": 0
     },
     "position": {  // Single position for multiple members!
       "x": 12.096878051757813,
       "y": 19.85175132751465,
       "z": -11.488070487976075
     }
   }
   ```

3. **Required Fix**
   The payload structure should be updated to include positions for all members:
   ```json
   {
     "currentGroups": {
       "members": ["Kaiden", "Goldie", "Noobster", "Diamond"],
       "npcs": 4,
       "players": 0
     },
     "positions": {
       "Kaiden": {
         "x": 12.096878051757813,
         "y": 19.85175132751465,
         "z": -11.488070487976075
       },
       "Goldie": {
         "x": 13.5,
         "y": 19.8,
         "z": -11.2
       },
       // ... positions for all members
     }
   }
   ```

4. **Collection Frequency**
   - All positions still updated every local state update (2 seconds)
   - Individual position changes tracked per entity
   - Movement threshold applied per entity 

### NPC Interaction Flow
1. **Proximity Detection System**
   ```lua
   -- Runs every 1 second in updateNPCs loop:
   function updateNPCs()
       while true do
           checkPlayerProximity()
           checkNPCProximity()
           checkOngoingConversations()
           wait(1)
       end
   end
   ```

2. **System Messages Types**
   ```lua
   -- Player proximity trigger
   "[SYSTEM] A player (%s) has entered your area. You can initiate a conversation if you'd like."
   
   -- NPC proximity trigger
   "[SYSTEM] Another NPC (%s) has entered your area. You can initiate a conversation if you'd like."
   ```

3. **Interaction Controls**
   - Cooldown system: 30 seconds between greetings
   - Active conversation tracking:
     ```lua
     activeConversations = {
         playerToNPC = {}, -- player UserId -> npcId
         npcToNPC = {},    -- npc Id -> npc Id
         npcToPlayer = {}  -- npc Id -> player UserId
     }
     ```
   - Response radius check for each NPC
   - Ability check ("initiate_chat" required)

4. **Flow Example - Player Detection**
   ```
   checkPlayerProximity runs →
   Player within NPC.responseRadius →
   Check NPC has initiate_chat ability →
   Check cooldowns and active conversations →
   Send system message →
   NPC can initiate conversation
   ```

5. **Flow Example - NPC Detection**
   ```
   checkNPCProximity runs →
   NPC2 within NPC1.responseRadius →
   Check NPC1 has initiate_chat ability →
   Check cooldowns and active conversations →
   Create mock participant →
   Send system message →
   NPC1 can initiate conversation
   ```

6. **Conversation Management**
   - Ongoing range checks
   - Automatic conversation ending when out of range
   - Cooldown tracking per pair of entities
   - Prevention of multiple simultaneous conversations 

### Range Detection Timing

1. **Update Frequency**
   - Main range checks run every 1 second
   - Three checks performed each cycle:
     ```lua
     checkPlayerProximity()  -- Player-NPC distances
     checkNPCProximity()     -- NPC-NPC distances
     checkOngoingConversations() -- Range-based conversation management
     ```

2. **Movement Updates** (runs in parallel)
   ```lua
   local function updateNPCMovement()
       while true do
           -- NPC movement checks and updates
           wait(5) -- Movement updates every 5 seconds
       end
   end
   ```

3. **Range Check Types**
   - **Player Proximity**: Every 1s, checks distance between each player and each NPC
   - **NPC Proximity**: Every 1s, checks distance between each NPC pair
   - **Conversation Range**: Every 1s, verifies participants are still in range
   - **Movement Opportunities**: Every 5s, checks if NPCs should move randomly

4. **Performance Impact**
   - Range checks are O(n²) for NPC-NPC checks
   - Range checks are O(n*m) for Player-NPC checks (n=NPCs, m=Players)
   - Each check requires position calculations and distance comparisons
   - Cooldown system prevents spam of interaction triggers 

### Conversation Tracking System

1. **Active Conversation State**
   ```lua
   -- Global state tracking all active conversations
   local activeConversations = {
       playerToNPC = {}, -- player UserId -> npcId
       npcToNPC = {},    -- npc Id -> npc Id
       npcToPlayer = {}  -- npc Id -> player UserId
   }
   ```

2. **Conversation Locking System**
   - **Lock Types**
     - **Conversation Lock**: Prevents receiving new [SYSTEM] proximity messages
     ```lua
     -- Example: NPC can't receive new proximity alerts if already in conversation
     if activeConversations.npcToNPC[npc1.id] then continue end
     if activeConversations.npcToPlayer[npc.id] then continue end
     ```
     
     - **Movement Lock**: NPCs won't do random movement while in conversation
     ```lua
     -- In updateNPCMovement:
     if canMove and not npc.isInteracting and 
        not activeConversations.npcToNPC[npc.id] and 
        not activeConversations.npcToPlayer[npc.id] then
         -- Only then can NPC move randomly
     end
     ```

   - **What Locking Prevents**
     - Cannot receive new [SYSTEM] proximity messages
     - Cannot initiate new conversations with other entities
     - Cannot perform random movement
     - Cannot be targeted for new conversations by other NPCs/players

   - **What Locking Allows**
     - Can still receive and process chat messages from current conversation partner
     - Can still move if forced by game mechanics
     - Can still be affected by other systems (damage, etc.)
     - Can still end conversation if participants move out of range

   - **Lock Duration**
     - Starts when conversation begins
     - Ends when:
       ```lua
       -- Any of these conditions:
       - Participants move out of range
       - Conversation explicitly ended
       - Server/game shutdown
       ```

   - **Lock Implementation**
     ```lua
     -- Three separate tracking mechanisms:
     activeConversations.npcToNPC[npc1.id] = {partner = npc2}    -- NPC-NPC lock
     activeConversations.npcToPlayer[npc.id] = player.UserId     -- NPC-Player lock
     activeConversations.playerToNPC[player.UserId] = npc.id     -- Player-NPC lock
     ```

3. **Mock Participant System**
   ```lua
   -- Creates a player-like object for NPC-NPC interactions
   function NPCManagerV3:createMockParticipant(npc)
       return {
           Name = npc.displayName,
           displayName = npc.displayName,
           UserId = npc.id,
           npcId = npc.id,
           Type = "npc",
           GetParticipantType = function() return "npc" end,
           GetParticipantId = function() return npc.id end,
           model = npc.model
       }
   end
   ```

4. **Usage Flow**
   ```lua
   -- When NPC2 enters NPC1's range:
   if not activeConversations.npcToNPC[npc1.id] then
       -- Create mock participant for NPC2
       local mockParticipant = npcManagerV3:createMockParticipant(npc2)
       
       -- Lock both NPCs in conversation
       activeConversations.npcToNPC[npc1.id] = {partner = npc2}
       activeConversations.npcToNPC[npc2.id] = {partner = npc1}
       
       -- Send system message using mock participant
       local systemMessage = string.format(
           "[SYSTEM] Another NPC (%s) has entered your area...",
           npc2.displayName
       )
       npcManagerV3:handleNPCInteraction(npc1, mockParticipant, systemMessage)
   end
   ```

5. **Conversation Prevention Rules**
   - NPCs can't start new conversations if:
     ```lua
     if activeConversations.npcToNPC[npc1.id] then continue end
     if activeConversations.npcToNPC[npc2.id] then continue end
     if activeConversations.npcToPlayer[npc.id] then continue end
     ```
   - Players can't start new conversations if:
     ```lua
     if activeConversations.playerToNPC[player.UserId] then return end
     ```

6. **Mock Participant Purpose**
   - Provides consistent interface for both player and NPC interactions
   - Allows NPCs to use same chat handling system as players
   - Maintains conversation state and identity information
   - Enables proper conversation tracking and cooldown management

7. **Conversation Cleanup**
   ```lua
   -- In checkOngoingConversations (runs every 1s):
   if not isInRange then
       npcManagerV3:endInteraction(npc1, npc2)
       -- Clears activeConversations entries
   end
   ```

### Conversation Limitations

1. **Exclusive 1-on-1 Conversations**
   ```lua
   -- Example scenario with 3 NPCs in range:
   NPC1 and NPC2 start conversation
   activeConversations.npcToNPC[npc1.id] = {partner = npc2}
   activeConversations.npcToNPC[npc2.id] = {partner = npc1}
   
   -- NPC3 is now blocked from:
   - Receiving chat messages from NPC1 or NPC2
   - Starting conversations with either NPC
   - Receiving [SYSTEM] messages about NPC1 or NPC2
   ```

2. **Group Conversation Limitations**
   - No support for group conversations (3+ participants)
   - Conversations are strictly paired
   - Other nearby NPCs are effectively "deaf" to ongoing conversations
   - Must wait for current conversation to end before interacting

3. **Potential Improvements**
   - Implement group conversation support
   - Allow "overhearing" nearby conversations
   - Enable NPCs to join existing conversations
   - Add priority system for conversation initiation 

### System Upgrade Plan

1. **Current System Analysis**
   - Backend supports group conversations but client enforces 1:1
   - Two competing proximity systems:
     ```lua
     -- Direct range checks (every 1s)
     local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
     local isInRange = distance <= npc.responseRadius
     
     -- Cluster-based system (every 10s)
     local clusters = InteractionService:getLatestClusters()
     ```
   - Timing issue: [SYSTEM] messages often precede cluster updates
   - Backend has group memory but it's not fully utilized

2. **Proposed Changes**

   A. **Remove 1:1 Conversation Lock**
   ```lua
   -- Replace current lock system:
   activeConversations.npcToNPC[npc1.id] = {partner = npc2}
   
   -- With group conversation tracking:
   activeGroups = {
       [clusterId] = {
           members = {},      -- All participating entities
           lastActivity = {}, -- Per-member timestamp
           messageQueue = {}, -- Optional: for handling multiple simultaneous messages
           state = "active"
       }
   }
   ```

   B. **Unified Proximity System**
   ```lua
   -- Single source of truth for proximity
   function checkProximity()
       local clusters = InteractionService:calculateClusters() -- Every 1s
       
       -- Check for cluster changes
       for clusterId, cluster in pairs(clusters) do
           if hasClusterChanged(clusterId, cluster) then
               -- 1. Send snapshot update
               GameStateService:syncClusterUpdate(cluster)
               
               -- 2. Send SYSTEM messages to all members
               for _, member in ipairs(cluster.members) do
                   sendGroupUpdateMessage(member, cluster)
               end
           end
       end
   end
   ```

3. **Message Handling Improvements**
   ```lua
   -- Group message broadcasting
   function broadcastToGroup(clusterId, message, sender)
       local cluster = activeGroups[clusterId]
       for _, member in ipairs(cluster.members) do
           if member.id ~= sender.id then
               -- Include sender name for backend processing
               local contextMessage = {
                   content = message,
                   sender = sender.Name,
                   group = cluster.members
               }
               sendMessageToMember(member, contextMessage)
           end
       end
   end
   ```

4. **Recommended Implementation Steps**
   1. Modify cluster calculation to run at 1s intervals
   2. Implement cluster change detection
   3. Remove conversation locking system
   4. Add group message broadcasting
   5. Update backend context creation to include all group members
   6. Add message queuing/handling system for group conversations

5. **Potential Challenges**
   - **Message Volume**: Many-to-many conversations could generate high message load
   - **Response Timing**: Multiple NPCs might try to respond simultaneously
   - **State Management**: Need to track conversation context for multiple participants
   - **Backend Load**: Increased API calls with group messages

6. **Suggested Solutions**
   - Implement message aggregation for group conversations
   - Add cooldown/turn-taking system:
     ```lua
     function canNPCRespond(npc, clusterId)
         local group = activeGroups[clusterId]
         local lastResponse = group.lastActivity[npc.id]
         return os.time() - lastResponse > MIN_RESPONSE_INTERVAL
     end
     ```
   - Use priority queue for message handling:
     ```lua
     messageQueue = {
         priority = {}, -- Immediate responses
         normal = {},   -- Regular conversation
         delayed = {}   -- Background responses
     }
     ```
   - Add rate limiting per cluster

7. **Expected Benefits**
   - More natural group conversations
   - Reduced latency in proximity detection
   - Better synchronization between proximity and messages
   - Fuller utilization of backend group capabilities
   - More realistic NPC interactions 

### Queue-Based Architecture Analysis

1. **Proposed Queue System**
   ```
   Client -> API Queue -> Worker -> LLM -> Response Queue -> Client
   ```
   
   ```lua
   -- Message structure in queue
   type QueuedMessage = {
       id: string,            -- Unique message ID
       clusterId: string,     -- Group context
       npcId: string,         -- Source NPC
       content: string,       -- Message content
       timestamp: number,     -- When queued
       priority: number,      -- Message priority
       context: {             -- Conversation context
           members: string[],
           recentMessages: Message[],
           relationships: table
       }
   }
   ```

2. **Queue Processing Flow**
   ```
   1. Client sends message
   ↓
   2. API stores in inbound queue (Redis/RabbitMQ)
   ↓
   3. Worker processes messages (can scale horizontally)
   ↓
   4. LLM generates response
   ↓
   5. Response stored in outbound queue
   ↓
   6. Client retrieves response
   ```

3. **Response Handling Options**

   A. **Polling System**
   ```lua
   -- Client-side polling
   function pollForResponses(messageId)
       while true do
           local response = ReplicatedStorage.GetQueuedResponse:InvokeServer(messageId)
           if response then
               handleNPCResponse(response)
               break
           end
           wait(0.1)
       end
   end
   ```

   B. **WebSocket Updates**
   ```lua
   -- Server pushes responses when available
   ReplicatedStorage.ResponseReceived.OnClientEvent:Connect(function(response)
       if response.targetNPC == currentNPC.id then
           handleNPCResponse(response)
       end
   end)
   ```

   C. **Hybrid Approach**
   ```lua
   local function handleResponse(messageId)
       -- Try immediate response first
       local response = tryGetImmediateResponse(messageId)
       if response then return response end
       
       -- Fall back to queue if needed
       return pollForResponse(messageId, MAX_POLL_TIME)
   end
   ```

4. **Benefits of Queue Architecture**
   - Horizontal scaling of message processing
   - Better handling of traffic spikes
   - Improved reliability through message persistence
   - Ability to prioritize messages
   - Reduced direct API load

5. **Implementation Challenges**
   ```lua
   -- Challenge: Message ordering
   local MessageOrderManager = {
       pendingMessages = {},
       
       addMessage = function(self, npcId, messageId)
           self.pendingMessages[npcId] = self.pendingMessages[npcId] or {}
           table.insert(self.pendingMessages[npcId], messageId)
       end,
       
       canDisplayMessage = function(self, npcId, messageId)
           local pending = self.pendingMessages[npcId]
           return pending and pending[1] == messageId
       end
   }
   ```

6. **Recommended Queue Structure**
   ```lua
   -- Multiple queue types for different priorities
   queues = {
       urgent = {
           maxLatency = 0.5,    -- Process within 500ms
           maxSize = 100,       -- Maximum queue size
           workers = 5          -- Dedicated workers
       },
       conversation = {
           maxLatency = 2,      -- Process within 2s
           maxSize = 1000,
           workers = 3
       },
       background = {
           maxLatency = 5,      -- Process within 5s
           maxSize = 5000,
           workers = 1
       }
   }
   ```

7. **Client Integration**
   ```lua
   function NPCManagerV3:handleQueuedChat(npc, message, clusterId)
       -- Generate unique message ID
       local messageId = HttpService:GenerateGUID()
       
       -- Send to queue
       local success = ReplicatedStorage.QueueMessage:InvokeServer({
           id = messageId,
           npcId = npc.id,
           clusterId = clusterId,
           content = message,
           priority = getPriority(message)
       })
       
       if success then
           -- Start polling or wait for WebSocket
           self:startResponseHandler(messageId, npc)
           
           -- Show temporary response
           self:showTypingIndicator(npc)
       end
   end
   ```

8. **Fallback Mechanisms**
   ```lua
   function handleChatResponse(npc, messageId)
       -- Try queue first
       local response = tryGetQueuedResponse(messageId)
       
       -- Fall back to direct API if queue fails
       if not response then
           response = fallbackToDirectAPI(npc, messageId)
       end
       
       -- Last resort: generic response
       if not response then
           response = generateLocalResponse()
       end
       
       return response
   end
   ```

This architecture would provide better scalability and reliability, but requires careful consideration of:
- Message ordering and delivery guarantees
- Client-side handling of delayed responses
- Fallback mechanisms for queue failures
- Proper error handling and recovery
- Monitoring and queue health metrics 

### Group Response Handling

1. **Broadcast Response Challenge**
   ```lua
   -- Current single-response model:
   local response = NPCChatHandler:HandleChat(request)
   -- ^ Problematic for group chats since multiple NPCs might respond
   
   -- Need to handle multiple potential responders:
   function broadcastAndGatherResponses(message, cluster)
       local responses = {}
       local respondingNPCs = {}
       
       -- Track who might respond
       for _, member in ipairs(cluster.members) do
           if canNPCRespond(member) then
               table.insert(respondingNPCs, member)
           end
       end
       
       return {
           expectedResponses = #respondingNPCs,
           responseTimeout = 5, -- seconds
           respondingNPCs = respondingNPCs
       }
   end
   ```

2. **Response Collection Strategies**

   A. **Aggregation Window**
   ```lua
   function collectGroupResponses(messageId, cluster)
       local responses = {}
       local startTime = os.time()
       
       -- Wait for either:
       -- 1. All expected responses
       -- 2. Maximum wait time
       -- 3. Priority response that should be shown immediately
       while os.time() - startTime < MAX_WAIT_TIME do
           local response = getNextQueuedResponse(messageId)
           if response then
               if response.priority == "immediate" then
                   return {response} -- Show high priority response immediately
               end
               table.insert(responses, response)
               if #responses >= cluster.expectedResponses then
                   break
               end
           end
           wait(0.1)
       end
       
       return responses
   end
   ```

   B. **Priority-Based Display**
   ```lua
   function handleGroupResponses(responses, cluster)
       -- Sort by response priority/relevance
       table.sort(responses, function(a, b)
           -- Consider:
           -- 1. Explicit priority
           -- 2. Relationship to speaker
           -- 3. Conversation context
           -- 4. Response timing
           return calculateResponsePriority(a) > calculateResponsePriority(b)
       end)
       
       -- Display responses with appropriate timing
       for i, response in ipairs(responses) do
           wait(calculateResponseDelay(i, response))
           displayNPCResponse(response)
       end
   end
   ```

3. **Response Timing Management**
   ```lua
   local ResponseTimingManager = {
       -- Track who's "typing" or about to respond
       activeResponders = {},
       
       addResponder = function(self, npcId, expectedDelay)
           self.activeResponders[npcId] = {
               startTime = os.time(),
               expectedResponse = os.time() + expectedDelay,
               typing = true
           }
           showTypingIndicator(npcId)
       end,
       
       -- Determine natural delays between responses
       calculateDelay = function(self, npc, messageLength)
           local baseDelay = messageLength * 0.1 -- 100ms per character
           local personalityFactor = npc.responseSpeed or 1
           return baseDelay * personalityFactor
       end
   }
   ```

4. **Display Orchestration**
   ```lua
   function orchestrateGroupResponses(responses, cluster)
       local displayQueue = {}
       
       -- Process all responses first
       for _, response in ipairs(responses) do
           local delay = ResponseTimingManager:calculateDelay(
               response.npc, 
               #response.message
           )
           
           table.insert(displayQueue, {
               response = response,
               displayTime = os.time() + delay,
               priority = response.priority
           })
       end
       
       -- Display in natural conversation flow
       while #displayQueue > 0 do
           local now = os.time()
           local nextResponse = table.remove(displayQueue, 1)
           
           if nextResponse.displayTime > now then
               wait(nextResponse.displayTime - now)
           end
           
           displayNPCResponse(nextResponse.response)
       end
   end
   ```

### WebSocket-Based Cluster Communication

1. **Dual WebSocket Architecture**
   ```
   Game Server
   ├── Outbound Socket (wss://api.example.com/clusters/outbound)
   │   └── Sends: Player/NPC messages, position updates, cluster changes
   │
   └── Inbound Socket (wss://api.example.com/clusters/inbound)
       └── Receives: NPC responses, cluster updates, system messages
   ```

2. **Message Channel Structure**
   ```lua
   -- Channel types for message routing
   channels = {
       cluster_updates = {
           -- Cluster membership changes
           pattern = "cluster:%s:update",
           handler = handleClusterUpdate
       },
       chat = {
           -- NPC/Player chat messages
           pattern = "chat:%s:message",
           handler = handleChatMessage
       },
       system = {
           -- System notifications
           pattern = "system:%s:notification",
           handler = handleSystemNotification
       }
   }
   ```

3. **Cluster-Based Routing**
   ```lua
   -- Each cluster gets its own channel
   local function subscribeToCluster(clusterId)
       local channel = string.format("cluster:%s:*", clusterId)
       inboundSocket:Send(JsonEncode({
           type = "subscribe",
           channel = channel
       }))
   end

   -- Message routing by cluster
   inboundSocket.OnMessage:Connect(function(message)
       local data = JsonDecode(message)
       if data.clusterId then
           local cluster = activeGroups[data.clusterId]
           if cluster then
               broadcastToCluster(cluster, data)
           end
       end
   end)
   ```

4. **Benefits of WebSocket Approach**
   - Real-time cluster updates
   - No polling needed
   - Natural group message broadcasting
   - Reduced server load
   - Better scalability per cluster

5. **Example Implementation**
   ```lua
   local WebSocketService = game:GetService("WebSocketService")
   
   local ClusterSocket = {
       outbound = nil,
       inbound = nil,
       activeChannels = {},
       
       init = function(self)
           -- Setup outbound connection
           self.outbound = WebSocketService:Connect(
               "wss://api.example.com/clusters/outbound"
           )
           
           -- Setup inbound connection
           self.inbound = WebSocketService:Connect(
               "wss://api.example.com/clusters/inbound"
           )
           
           self:setupHandlers()
       end,
       
       sendGroupMessage = function(self, clusterId, message)
           self.outbound:Send(JsonEncode({
               type = "chat",
               clusterId = clusterId,
               content = message,
               timestamp = os.time()
           }))
       end,
       
       handleInbound = function(self, message)
           local data = JsonDecode(message)
           
           -- Route to appropriate handler
           if data.type == "chat" then
               self:handleChatMessage(data)
           elseif data.type == "cluster_update" then
               self:handleClusterUpdate(data)
           end
       end
   }
   ```

6. **Cluster Management**
   ```lua
   -- When cluster changes are detected
   function onClusterChanged(oldCluster, newCluster)
       -- Unsubscribe from old cluster
       if oldCluster then
           ClusterSocket:unsubscribe(oldCluster.id)
       end
       
       -- Subscribe to new cluster
       if newCluster then
           ClusterSocket:subscribe(newCluster.id)
           
           -- Notify all members
           for _, member in ipairs(newCluster.members) do
               sendSystemMessage(member, "cluster_joined", {
                   clusterId = newCluster.id,
                   members = newCluster.members
               })
           end
       end
   end
   ```

7. **Advantages for Group Chat**
   - Messages instantly broadcast to all cluster members
   - Natural handling of multiple simultaneous responses
   - Built-in support for cluster-wide events
   - Reduced complexity in message routing
   - Better state synchronization 

### Recommended Two-Phase Upgrade

1. **Phase 1: Quick Multi-User Enable**
   ```lua
   -- Remove conversation locks but keep tracking
   local activeConversations = {
       participants = {}, -- track who's talking but don't lock
       clusters = {}     -- track cluster membership
   }
   
   -- Modified proximity check (allows multiple conversations)
   function checkNPCProximity()
       for _, npc1 in pairs(npcs) do
           for _, npc2 in pairs(npcs) do
               if npc1.id ~= npc2.id then
                   -- Check distance as before
                   local distance = (npc1.model.PrimaryPart.Position - 
                                   npc2.model.PrimaryPart.Position).Magnitude
                   
                   if distance <= npc1.responseRadius then
                       -- Just track participants without locking
                       activeConversations.participants[npc1.id] = true
                       activeConversations.participants[npc2.id] = true
                       
                       -- Send system message as before
                       local systemMessage = string.format(
                           "[SYSTEM] Another NPC (%s) has entered your area...",
                           npc2.displayName
                       )
                       -- Allow message even if already in conversation
                       npcManagerV3:handleNPCInteraction(npc1, mockParticipant, systemMessage)
                   end
               end
           end
       end
   end
   ```

2. **Phase 2: WebSocket Implementation**
   - Implement after multi-user is working
   - Provides better scaling and real-time updates
   - Handles group chat more elegantly
   - Better cluster state management

3. **Benefits of This Approach**
   - Quick enablement of multi-user chat
   - Minimal code changes for Phase 1
   - Can test group dynamics before WebSocket
   - Gradual migration path
   - Maintains existing functionality 

### Interim Cluster-Aware System Messages

1. **Enhanced System Message**
   ```lua
   function createEnhancedSystemMessage(npc, participant, cluster)
       return {
           type = "system",
           content = string.format(
               "[SYSTEM] %s has entered your area...",
               participant.displayName
           ),
           cluster_data = {
               id = cluster.id,
               members = cluster.members,
               formed = os.time(),
               positions = cluster.positions,
               relationships = cluster.relationships
           },
           -- Include full context for immediate use
           context = {
               location = cluster.location,
               participants = cluster.members,
               timestamp = os.time()
           }
       }
   end
   ```

2. **Modified Proximity Check**
   ```lua
   function checkNPCProximity()
       -- Get current clusters first
       local clusters = InteractionService:getLatestClusters()
       
       for clusterId, cluster in pairs(clusters) do
           -- For each new member that hasn't received notification
           for _, member in ipairs(cluster.members) do
               if not hasReceivedClusterNotification(member.id, clusterId) then
                   -- Send enhanced system message with full cluster data
                   local systemMessage = createEnhancedSystemMessage(
                       member,
                       cluster.members,
                       cluster
                   )
                   
                   -- This will update NPC's group memory immediately
                   npcManagerV3:handleNPCInteraction(member, mockParticipant, systemMessage)
                   
                   markClusterNotificationSent(member.id, clusterId)
               end
           end
       end
   end
   ```

3. **Benefits**
   - Immediate group context availability
   - No wait for snapshot sync
   - Single source of truth (cluster system)
   - Maintains existing message flow
   - No major architectural changes needed

4. **Implementation Notes**
   - System messages become self-contained with cluster data
   - API can update group memory immediately
   - Reduces race conditions with snapshot system
   - Preserves existing conversation mechanics 

### Alternative Cluster Sync Approach

1. **Immediate Cluster Snapshot**
   ```lua
   function handleClusterChange(cluster)
       -- 1. Send immediate snapshot for just this cluster
       GameStateService:syncSingleCluster({
           clusterId = cluster.id,
           members = cluster.members,
           positions = cluster.positions,
           timestamp = os.time()
       })
       
       -- 2. Wait for snapshot confirmation
       local success = waitForSnapshotConfirm(cluster.id)
       
       -- 3. Then send system messages
       if success then
           for _, member in ipairs(cluster.members) do
               local systemMessage = string.format(
                   "[SYSTEM] %s has entered your area...",
                   member.displayName
               )
               npcManagerV3:handleNPCInteraction(member, mockParticipant, systemMessage)
           end
       end
   end
   ```

2. **Benefits**
   - Simpler than enhancing system messages
   - Uses existing snapshot processing
   - Guarantees cluster data is updated before messages
   - Maintains separation of concerns
   - No changes needed to message format

3. **Implementation**
   ```lua
   -- Add to GameStateService
   function GameStateService:syncSingleCluster(clusterData)
       return self:syncWithBackend({
           type = "cluster_update",
           data = clusterData,
           priority = "immediate"
       })
   end
   
   -- Modified proximity check
   function checkNPCProximity()
       local clusters = InteractionService:getLatestClusters()
       for clusterId, cluster in pairs(clusters) do
           if hasClusterChanged(clusterId, cluster) then
               handleClusterChange(cluster)
           end
       end
   end
   ```

4. **Advantages Over Enhanced Messages**
   - Uses existing snapshot pathway
   - Cleaner separation between state and messaging
   - More reliable state management
   - Easier to debug and maintain 