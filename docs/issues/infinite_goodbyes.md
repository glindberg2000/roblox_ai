# Infinite Goodbyes Issue

## Problem Description
Two critical issues are occurring with NPC conversations:

1. **NPC-NPC Infinite Goodbye Loop**
   - When two NPCs end a conversation, they get stuck in an infinite loop of saying goodbye to each other
   - Each NPC responds to the other's "Goodbye" with another "Goodbye"
   - This creates spam in the chat and keeps NPCs locked in non-productive interactions

2. **Player-NPC Premature Endings**
   - Player conversations with NPCs are ending prematurely
   - NPCs sometimes go silent or abruptly end conversations with players
   - This creates a poor user experience as conversations feel unnatural

## Detailed Implementation Steps

### 1. Add Goodbye State Tracking
```lua
-- Add to NPCManagerV3.lua near instance variables
NPCManagerV3.activeGoodbyes = {} -- Tracks ongoing goodbye states
```

### 2. Update Participant Type Detection
```lua
function NPCManagerV3:processAIResponse(npc, participant, response)
    -- More reliable participant type detection
    local participantType = "player"  -- Default to player
    if typeof(participant) ~= "Instance" or not participant:IsA("Player") then
        if participant.npcId and self.npcs[participant.npcId] then
            participantType = "npc"
        end
    end
    
    -- Rest of function...
end
```

### 3. Separate Player and NPC Logic
```lua
-- For players: Never end conversation
if participantType == "player" then
    if response.metadata then
        response.metadata.should_end = nil  -- Clear any end flags
    end
    
    if response.message then
        self:displayMessage(npc, response.message, participant)
    end
    return
end

-- For NPCs: Handle goodbye state
if participantType == "npc" then
    if response.metadata and response.metadata.should_end then
        local convKey = npc.id .. "_" .. participant.npcId
        
        -- Only say goodbye if we haven't already
        if not self.activeGoodbyes[convKey] then
            self.activeGoodbyes[convKey] = os.time()
            self.conversationCooldowns[convKey] = os.time()
            self:displayMessage(npc, "Goodbye! Talk to you later!", participant)
        end
        return
    end
end
```

### 4. Add Cleanup Task
```lua
-- Add to initialization or after activeGoodbyes declaration
task.spawn(function()
    while true do
        task.wait(60)  -- Check every minute
        local now = os.time()
        for convKey, timestamp in pairs(NPCManagerV3.activeGoodbyes) do
            if now - timestamp > 300 then  -- 5 minute cooldown
                NPCManagerV3.activeGoodbyes[convKey] = nil
            end
        end
    end
end)
```

### 5. Update API Handling
In `letta_router.py`:
```python
@router.post("/chat/v2", response_model=ChatResponse)
async def chat_with_npc_v2(request: ChatRequest):
    # Ensure participant type defaults to player
    participant_type = request.context.get("participant_type", "player")
    if participant_type not in ["player", "npc"]:
        participant_type = "player"
    
    # Only include should_end for NPC-NPC conversations
    metadata = {
        "participant_type": participant_type,
        "interaction_id": request.context.get("interaction_id"),
        "is_npc_chat": participant_type == "npc"
    }
    
    if participant_type == "npc":
        metadata["should_end"] = response.get("should_end", False)
    
    return ChatResponse(
        message=message,
        metadata=metadata,
        action={"type": "none"}
    )
```

## Validation Steps

1. **NPC-NPC Conversation Test**
   - Start NPC-to-NPC conversation
   - Verify only one goodbye is sent
   - Confirm conversation ends without loops
   - Check cooldown prevents immediate restart

2. **Player-NPC Conversation Test**
   - Start player-NPC conversation
   - Verify no premature endings
   - Confirm all messages display properly
   - Test conversation continues after AI suggests ending

3. **Edge Cases**
   - Test multiple NPCs talking simultaneously
   - Verify player can interrupt NPC conversations
   - Check conversation state after range/distance changes

## Expected Results

1. **NPC-NPC Conversations**
   - One NPC says goodbye
   - Other NPC doesn't respond with goodbye
   - Conversation ends cleanly
   - Cooldown prevents immediate restart

2. **Player-NPC Conversations**
   - No automatic goodbyes
   - Continuous conversation flow
   - Only ends when player leaves range
   - No premature endings

## Related Files
- `games/sandbox-v1/src/shared/NPCManagerV3.lua`
- `api/app/letta_router.py`

## Next Steps
1. [ ] Implement changes in NPCManagerV3.lua
2. [ ] Update API response handling
3. [ ] Test all conversation scenarios
4. [ ] Monitor logs for unexpected behavior
5. [ ] Consider implementing distance-based ending for NPC-NPC chats
