# NPC Group Conversation Coordination

## Current System Architecture

### Components
1. **Roblox/Lua Client**
   - Handles NPC positioning and movement
   - Manages visual chat bubbles and chat UI
   - Tracks NPC clusters based on proximity
   - Sends/receives messages via RemoteEvents

2. **Backend API**
   - Processes NPC chat requests
   - Maintains conversation context
   - Handles NPC decision making
   - Returns responses and actions

3. **Letta LLM**
   - Processes natural language
   - Generates contextual responses
   - Understands group dynamics
   - Makes conversation decisions

### Key Features
1. **Cluster System**
   - NPCs are grouped by proximity
   - Clusters update in real-time
   - Members share conversation context
   - Enables group-aware interactions

2. **Snapshot System**
   - Regular state updates to backend
   - Includes cluster composition
   - Tracks conversation history
   - Updates block memory

3. **Group-Aware NPCs**
   - Can perceive multiple participants
   - Understand group context
   - React to cluster changes
   - Participate in group conversations

## Current Challenges

### 1. Conversation Initiation
- System messages trigger NPC responses
- Multiple NPCs might respond simultaneously
- Need balance between responsiveness and chaos
- Question of who should speak first

### 2. Message Propagation
- Messages replicate to all cluster members
- Can lead to message flooding
- Each NPC might want to respond
- Need orderly conversation flow

### 3. State Management
- Cluster changes affect conversation state
- Active conversations vs. new groups
- When to send system messages
- How to handle member joins/leaves

### 4. Backend Communication
- API calls require triggers
- Latency considerations
- Batch processing limitations
- Response coordination

## Current Behavior

1. **When New Cluster Forms**
   ```
   - Cluster forms/changes
   - System message sent to all NPCs
   - Each NPC can respond
   - Messages propagate to group
   ```

2. **During Active Conversation**
   ```
   - New member joins cluster
   - Block memory updates
   - Existing conversation continues
   - New member can join in
   ```

## Key Questions

1. **Initiation Control**
   - How to decide which NPC speaks first?
   - Should we rotate system messages?
   - How to handle no-response scenarios?

2. **Message Flow**
   - How to prevent message flooding?
   - How to maintain conversation coherence?
   - How to handle simultaneous responses?

3. **State Synchronization**
   - When to update backend state?
   - How to handle state conflicts?
   - How to maintain conversation context?

## Potential Solutions

1. **Selective System Messages**
   - Send to one NPC at a time
   - Use cooldown system
   - Try next NPC if no response

2. **Backend Coordination**
   - Let API control response order
   - Maintain group conversation state
   - Coordinate multiple speakers

3. **Hybrid Approach**
   - Use system messages for initiation
   - Let natural conversation flow continue
   - Backend manages active conversations

## Discussion Points

1. **Balance Considerations**
   - Natural conversation flow vs. control
   - Responsiveness vs. order
   - Group dynamics vs. individual agency

2. **Technical Constraints**
   - API call frequency
   - State management complexity
   - Real-time requirements

3. **User Experience**
   - Conversation naturalness
   - Group interaction coherence
   - Response timing

## Next Steps

1. Determine preferred coordination approach
2. Define specific implementation rules
3. Consider edge cases and failure modes
4. Plan testing scenarios

## Open Questions

1. Should we implement conversation priority/roles?
2. How to handle conversation transitions?
3. What metrics define successful group chat?
4. How to balance autonomy and coordination?

## Expert Consultation

### Professor Synapse Questions
🧙🏾‍♂️ **Professor Synapse:**
Before we move forward, let me gather more context and clarify your goals:
1. Which aspect of the system is the highest priority to solve right now?
2. Are you aiming for a purely system-driven approach or a more natural, emergent conversation flow among NPCs?
3. Do you foresee using a single, centralized process to coordinate conversation or do you want each NPC to have more autonomy?
4. Any specific success criteria?

**Response:**
1. **Highest Priority**
   - The critical issue is the conversation trigger mechanism
   - Currently, system messages are needed to trigger NPC responses via API calls
   - Without these triggers, NPCs can't initiate or join conversations
   - But sending system messages to all NPCs causes flooding

2. **System vs Natural Flow**
   - The backend (Letta) already handles natural conversation flow well
   - The issue is more about the mechanical trigger system
   - We want to maintain natural flow while solving the technical trigger problem
   - Current system messages feel artificial ("NPC has entered your area")

3. **Coordination Approach**
   - The backend already has good group awareness through block memory
   - NPCs make autonomous decisions about when/how to respond
   - The challenge is in the Lua/API bridge mechanism
   - Need efficient way to let NPCs "notice" changes and respond

4. **Success Criteria**
   - Minimize unnecessary API calls
   - Maintain conversation coherence
   - Avoid message flooding when clusters change
   - Keep the natural feel of NPC interactions

### Current Implementation Details
🤖 **Expert Analysis of Current System:**

Current trigger system implementation:

1. **Cluster Updates (Every Second)**
```lua
-- In InteractionService
local CLUSTER_UPDATE_INTERVAL = 1 -- Update clusters every second

function InteractionService:logProximityMatrix(npcs)
    -- Calculate distances and form clusters
    -- Store new clusters
    lastClusters = clusters
    lastUpdateTime = os.time()
end
```

2. **System Message Triggers**
```lua
function InteractionService:handleClusterChanges(oldClusters, newClusters)
    for _, newCluster in ipairs(newClusters) do
        -- Currently sends to ALL NPCs in cluster
        for _, member in ipairs(newCluster.members) do
            NPCManagerV3:sendSystemMessage(member, {
                type = "cluster_update",
                members = newCluster.members
            })
        end
    end
end
```

3. **Message Propagation**
```lua
function NPCManagerV3:handleNPCInteraction(npc, participant, message)
    -- When any NPC responds, message gets sent to ALL cluster members
    local response = NPCChatHandler:HandleChat({
        message = message,
        npc_id = npc.id,
        context = {
            nearby_players = self:getVisiblePlayers(npc),
            interaction_history = {} -- Recent messages
        }
    })
    
    if response then
        -- Broadcasts to all NPCs in cluster
        self:processAIResponse(npc, participant, response)
    end
end
```

Key Issues Identified:
1. System messages fire every time clusters update (every second)
2. Each NPC in cluster receives system message
3. Each response gets broadcast to all NPCs
4. Each NPC might generate new API call in response 

## System Flow Analysis

### 1. Trigger Points
1. **Cluster Formation/Changes** (Every 1s)
   ```
   InteractionService:logProximityMatrix
   → Calculate new clusters
   → Compare with lastClusters
   → If changes detected → handleClusterChanges
   → Sends system messages to ALL NPCs in cluster
   ```

2. **Player Clicks NPC**
   ```
   NPCManagerV3:setupClickDetector
   → Creates system message "[SYSTEM] Player X clicked..."
   → handleNPCInteraction
   → Makes API call to get NPC response
   ```

3. **NPC Receives Message**
   ```
   handleNPCInteraction
   → Checks for duplicate messages
   → Makes API call to get NPC response
   → If response, broadcasts to all cluster members
   → Each NPC might make new API call in response
   ```

### 2. Message Routing
1. **System Messages**
   ```
   Lua → All NPCs in cluster
   → Each NPC makes separate API call
   → Each response broadcasts to cluster
   → Can trigger cascade of responses
   ```

2. **Chat Messages**
   ```
   NPC/Player sends message
   → Lua broadcasts to cluster
   → Each NPC receives message
   → Each makes API call for potential response
   → Responses broadcast back to cluster
   ```

3. **Backend Updates**
   ```
   Regular snapshots update block memory
   → NPCs aware of group changes
   → But can't respond without trigger
   → Need system message or chat to respond
   ```

### 3. API Communication
1. **HTTP Calls Made When:**
   - System message received
   - Chat message received
   - Player clicks NPC
   - NPC receives broadcast message

2. **API Response Contains:**
   - NPC's response message
   - Actions to take
   - Updated memory/state

3. **Response Processing:**
   ```
   API returns response
   → Lua processes response
   → Creates chat bubble
   → Broadcasts to cluster
   → Can trigger more API calls
   ```

### 4. Current Pain Points
1. **Trigger Cascade:**
   ```
   Cluster changes
   → System messages to all
   → Multiple API calls
   → Multiple responses
   → Each response triggers more potential responses
   ```

2. **Redundant Updates:**
   ```
   Block memory already has group info
   → But needs system message to respond
   → Results in duplicate state tracking
   ```

3. **Message Flooding:**
   ```
   One NPC responds
   → All NPCs receive message
   → All might try to respond
   → No coordination of responses
   ``` 

## Proposed Quick Solution

### 1. Selective System Messages
Instead of broadcasting to all NPCs, implement a responder selection system:

```lua
function selectResponder(cluster)
    local bestScore = -1
    local selectedNPC = nil
    
    for _, memberName in ipairs(cluster.members) do
        local npc = getNPCByName(memberName)
        if npc then
            -- Simple scoring formula
            local score = 0
            score = score + (npc.energy or 0) * 0.4
            score = score + (npc.health or 100) * 0.3
            score = score + (math.random() * 0.3)
            
            if score > bestScore then
                bestScore = score
                selectedNPC = npc
            end
        end
    end
    return selectedNPC
end
```

### 2. Benefits of This Approach
1. **Uses Existing Systems**
   - Leverages current SILENCE mode
   - Works with existing message routing
   - Minimal changes to core architecture

2. **Reduces Message Flood**
   - Only one NPC receives system message
   - Others still receive chat messages
   - Natural conversation flow maintained

3. **Simple but Flexible**
   - Scoring can be adjusted easily
   - Could add more factors (personality, role, etc.)
   - Random factor prevents predictability

### 3. Implementation Steps
1. Add responder selection function
2. Modify cluster change handler
3. Keep existing message propagation
4. Use SILENCE mode for response control

### 4. Future Enhancements
1. More sophisticated scoring
2. Response cooldowns
3. Role-based selection
4. Conversation queuing
5. Multiple Letta instances if needed

This approach provides a quick improvement while leaving room for more sophisticated solutions later. 

## Current State Issues

### Memory State Inconsistencies
1. **Snapshot System Shows:**
   ```
   Cluster 1: ['Kaiden', 'greggytheegg', 'Goldie', 'Noobster', 'Diamond']
   ```

2. **Agent Memories Show:**
   - Goldie: "Noobster, Diamond"
   - Diamond: "Goldie, Noobster"
   - Kaiden: Empty group
   - Noobster: "Goldie, Diamond"

3. **Potential Issues:**
   - Group state updates not properly synchronized
   - Memory updates might be overwriting each other
   - Join/leave events causing state conflicts
   - Verification check between Lua and backend may be faulty

### Investigation Needed
1. Verify how group updates are processed in LettaDev
2. Check memory block update logic
3. Review snapshot integration process
4. Examine join/leave event handling 

## LettaDev Debugging Tools

### 1. State Verification
The backend provides tools to verify group state consistency:

```python
def verify_group_state(client, agent_ids, snapshot_data):
    """Debug helper to check group state consistency"""
    print("\nSnapshot vs Memory State Check:")
    
    # 1. Print snapshot state
    print(f"\nSnapshot shows cluster:")
    print(json.dumps(snapshot_data.cluster_members, indent=2))
    
    # 2. Check each agent's memory
    for agent_id in agent_ids:
        group_block = get_memory_block(client, agent_id, "group_members")
        print(f"\nAgent {agent_id} memory shows:")
        print(json.dumps(group_block, indent=2))
        
        # Highlight inconsistencies
        memory_members = set(group_block["members"].keys())
        snapshot_members = set(m["id"] for m in snapshot_data.cluster_members)
        
        if memory_members != snapshot_members:
            print("\nMismatch detected!")
            print(f"Missing in memory: {snapshot_members - memory_members}")
            print(f"Extra in memory: {memory_members - snapshot_members}")
```

### 2. Common Issues & Solutions

1. **Memory Update Pattern**
   ```python
   # WRONG: Direct update can overwrite other changes
   update_memory_block(client, agent_id, "group_members", new_group_data)

   # CORRECT: Merge with existing state
   current_group = get_memory_block(client, agent_id, "group_members")
   current_group["members"].update(new_members)
   update_memory_block(client, agent_id, "group_members", current_group)
   ```

2. **Group State Synchronization**
   ```python
   def sync_group_state(client, cluster_id, snapshot_data):
       """Ensure all NPCs in cluster have same group state"""
       # Build canonical state
       canonical_members = {
           player["id"]: {
               "name": player["name"],
               "appearance": player.get("appearance", ""),
               "notes": player.get("notes", "")
           }
           for player in snapshot_data.cluster_members
       }
       
       # Update all NPCs
       for agent_id in snapshot_data.cluster_npcs:
           current = get_memory_block(client, agent_id, "group_members")
           current["members"] = canonical_members
           current["last_updated"] = datetime.now().isoformat()
           update_memory_block(client, agent_id, "group_members", current)
   ```

### 3. Health Checks
Regular verification of group state consistency:

```python
def run_group_health_check(client, cluster_id):
    """Regular health check for group state"""
    npcs = get_cluster_npcs(cluster_id)
    
    # Compare group states
    states = {}
    for npc in npcs:
        group = get_memory_block(client, npc.agent_id, "group_members")
        states[npc.agent_id] = set(group["members"].keys())
    
    # Find inconsistencies
    reference_state = next(iter(states.values()))
    mismatched = {
        npc_id: members 
        for npc_id, members in states.items() 
        if members != reference_state
    }
    
    if mismatched:
        print("Found state mismatches:")
        for npc_id, members in mismatched.items():
            print(f"NPC {npc_id}: {members}")
        return False
    return True
```

### Next Steps for Debugging
1. Run `verify_group_state` to identify specific inconsistencies
2. Implement proper merge-based updates
3. Add regular health checks
4. Consider adding state synchronization on cluster changes 