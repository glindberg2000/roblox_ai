# NPC Chat System Documentation

## Current System (Synchronous)
The current implementation uses direct request-response patterns for NPC chat interactions.

### Immediate Fixes Needed
1. **Message Delivery System**
   ```lua
   -- Basic message testing endpoint
   function ChatService:testMessage(npcId: string, message: string)
       local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
       NPCChatEvent:FireAllClients({
           type = "CHAT",
           npcName = npcId,
           message = message,
           context = { test = true }
       })
   end
   ```

2. **Simple Event System**
   ```lua
   local ChatEvents = {
       MessageSent = Instance.new("BindableEvent"),
       MessageReceived = Instance.new("BindableEvent"),
       MessageCompleted = Instance.new("BindableEvent")
   }
   ```

3. **Testing Protocol**
   - Add direct test command
   - Verify event flow
   - Check client reception
   - Validate chat bubble display

4. **Message Queue Service Implementation**
   ```lua
   local MessageQueueService = {}
   local ReplicatedStorage = game:GetService("ReplicatedStorage")
   local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
   local lastMessageTimes = {}
   
   function MessageQueueService:enqueueMessage(npcName, text, cooldown)
       local now = tick()
       cooldown = cooldown or 5
       
       if not lastMessageTimes[npcName] or now - lastMessageTimes[npcName] > cooldown then
           NPCChatEvent:FireAllClients({
               npcName = npcName,
               message = text,
               type = "npc_chat"
           })
           lastMessageTimes[npcName] = now
           return true
       end
       return false
   end
   
   return MessageQueueService
   ```

5. **Integration Points**
   ```lua
   -- In GameStateService or similar
   local function heartbeatHandler()
       local success = syncWithBackend()
       if success then
           MessageQueueService:enqueueMessage("Diamond", "Vive Libre", 10)
       end
   end
   ```

6. **Testing Sequence**
   1. Implement basic MessageQueueService
   2. Add test command to trigger message
   3. Verify cooldown behavior
   4. Test client reception
   5. Validate chat display

### Key Concepts to Preserve
1. **Message Throttling**
   - Track last message time per NPC
   - Enforce cooldown periods
   - Prevent message spam

2. **Centralized Event Dispatch**
   - Single point of message distribution
   - Consistent payload structure
   - Type-based message handling

3. **Event-Driven Architecture**
   - Decouple message generation from display
   - Support multiple trigger sources
   - Maintain clean separation of concerns

### Limitations
- High latency during peak loads
- Potential for dropped messages
- No queue management
- Limited status feedback
- Blocking operations impact performance

### Previous Implementation Challenges
1. **Client-Side State Management**
   - Messages dropped during high load periods
   - Client/server state desynchronization
   - Race conditions with multiple NPC chats
   - Unmanaged chat bubble queuing

2. **Performance Issues**
   - Blocking operations causing lag
   - No message prioritization
   - Inefficient chat bubble rendering
   - Memory leaks from uncleaned chat states

3. **Error Handling**
   - Incomplete error recovery
   - Missing retry mechanisms
   - Poor error visibility
   - Inconsistent state after errors

### Solutions in New Queue System
1. **Robust State Management**
   - Server-side queue as source of truth
   - Client-side state cache with version tracking
   - Ordered message processing
   - Proper chat bubble lifecycle management

2. **Performance Optimizations**
   - Async message processing
   - Batched updates
   - Prioritized message queue
   - Memory-efficient state tracking

3. **Error Resilience**
   - Automatic retry mechanism
   - State recovery procedures
   - Clear error reporting
   - Graceful degradation options

## Planned Async Queue System

### Architecture Overview
1. **Client Layer**
   - Chat UI components
   - Queue status indicators
   - State management
   - Polling/subscription system

2. **Server Layer**
   - Queue management
   - Request batching
   - State persistence
   - Status monitoring

3. **Shared Components**
   - Queue data structures
   - Status types/enums
   - Logging system

### Implementation Plan

#### Phase 1: Queue Infrastructure
- [ ] Create queue data structures
- [ ] Implement server-side queue management
- [ ] Add basic status monitoring
- [ ] Update logging for queue operations

#### Phase 2: Server Modifications
- [ ] Convert chat handlers to async
- [ ] Implement request batching
- [ ] Add throttling mechanisms
- [ ] Create queue status endpoints
- [ ] Add state persistence

#### Phase 3: Client Updates
- [ ] Add queue status UI
- [ ] Implement polling system
- [ ] Create chat state management
- [ ] Add loading/status indicators

#### Phase 4: Testing & Optimization
- [ ] Load testing
- [ ] Queue performance metrics
- [ ] Latency monitoring
- [ ] Error handling improvements

### Technical Details

#### Queue Data Structure
```lua
type QueueEntry = {
    id: string,
    npcId: string,
    message: string,
    timestamp: number,
    status: QueueStatus,
    priority: number,
    metadata: {
        conversationId: string?,
        context: any
    }
}

enum QueueStatus {
    PENDING = "PENDING",
    PROCESSING = "PROCESSING",
    COMPLETED = "COMPLETED",
    FAILED = "FAILED"
}
```

#### Server-Side Components
```lua
ChatQueueManager = {
    addToQueue: (entry: QueueEntry) -> boolean,
    processQueue: () -> void,
    getStatus: (id: string) -> QueueStatus,
    batchProcess: (count: number) -> void
}
```

#### Client-Side Components
```lua
ChatQueueClient = {
    submitMessage: (message: string) -> string, -- Returns queue ID
    getStatus: (queueId: string) -> QueueStatus,
    subscribe: (callback: (QueueEntry) -> void) -> void
}
```

### Migration Strategy
1. Implement queue system alongside current system
2. Gradually migrate NPCs to queue system
3. Monitor performance and errors
4. Full cutover once stable

### Monitoring & Debugging
- Queue length metrics
- Processing time tracking
- Error rate monitoring
- Status distribution
- Batch processing stats

### Configuration Options
```lua
QUEUE_CONFIG = {
    maxQueueSize: number,
    batchSize: number,
    pollInterval: number,
    maxRetries: number,
    timeoutSeconds: number
}
```

## Future Considerations
- Real-time updates via WebSocket
- Priority queue system
- Multi-server scaling
- Advanced batching strategies
- Persistent chat history

## Development Guidelines
1. Use typed interfaces where possible
2. Add comprehensive logging
3. Include status monitoring
4. Handle edge cases gracefully
5. Document all queue operations

## Testing Requirements
1. Queue overflow handling
2. Network failure recovery
3. State persistence verification
4. Load testing scenarios
5. Error condition handling

## Minimal Test Implementation

### Phase 1: Basic Message Broadcasting
```lua
-- In ReplicatedStorage.Shared.NPCSystem.services.MessageQueueService
local MessageQueueService = {}
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(script.Parent.LoggerService)

-- Simple state tracking
local lastMessageTimes = {}
local COOLDOWN = 5

function MessageQueueService:enqueueMessage(npcName, text)
    local now = tick()
    if not lastMessageTimes[npcName] or now - lastMessageTimes[npcName] >= COOLDOWN then
        -- Get or create event
        local NPCChatEvent = ReplicatedStorage:FindFirstChild("NPCChatEvent") or
            Instance.new("RemoteEvent", ReplicatedStorage)
        NPCChatEvent.Name = "NPCChatEvent"
        
        -- Send message
        NPCChatEvent:FireAllClients({
            npcName = npcName,
            message = text,
            type = "npc_chat"
        })
        
        lastMessageTimes[npcName] = now
        LoggerService:debug("CHAT", string.format("Message sent for %s: %s", npcName, text))
        return true
    end
    return false
end

return MessageQueueService
```

### Phase 2: Simple Client Handler
```lua
-- In StarterPlayerScripts.NPCClientHandler
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
local ChatService = game:GetService("Chat")

NPCChatEvent.OnClientEvent:Connect(function(data)
    if not (data and data.npcName and data.message) then return end
    
    -- Find NPC
    local npcModel = workspace.NPCs:FindFirstChild(data.npcName)
    if not npcModel or not npcModel:FindFirstChild("Head") then return end
    
    -- Show bubble chat
    ChatService:Chat(npcModel.Head, data.message)
    
    -- Also show in chat window
    game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
        Text = string.format("[%s]: %s", data.npcName, data.message)
    })
end)
```

### Phase 3: Test Command
```lua
-- In ServerScriptService.TestCommands
local MessageQueueService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.MessageQueueService)

game:GetService("Players").PlayerAdded:Connect(function(player)
    player.Chatted:Connect(function(message)
        if message == "/testchat Diamond" then
            MessageQueueService:enqueueMessage("Diamond", "Vive Libre")
        end
    end)
end)
```

### Validation Steps
1. Start in Studio
2. Verify RemoteEvent exists
3. Run `/testchat Diamond`
4. Check:
   - Message appears in bubble
   - Message appears in chat window
   - Cooldown blocks spam
   - No errors in output

### Next Steps (Only If Basic Test Works)
1. Add heartbeat message test
2. Test with multiple NPCs
3. Consider queue enhancements

### Implementation Notes
1. **Keep Initial Test Minimal**
   - Only implement MessageQueueService + RemoteEvent + cooldown
   - Skip advanced features (async queue, batch processing) for now
   - Focus on getting one NPC to say "Vive Libre" reliably

2. **Potential Issues to Watch**
   - NPC model might not be loaded when message arrives
   - Multiple chat systems might cause double messages
   - Workspace.NPCs folder must exist
   - Head part must be available for bubble chat

3. **Quick Fixes If Issues Occur**
   ```lua
   -- Add basic error handling
   local success, err = pcall(function()
       ChatService:Chat(npcModel.Head, data.message)
   end)
   if not success then
       -- Fallback to just system chat
       game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
           Text = string.format("[%s]: %s", data.npcName, data.message)
       })
   end
   ```