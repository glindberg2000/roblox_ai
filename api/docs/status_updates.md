# NPC Status & Group Update System

## Overview
The NPC status and group update system spans both the Lua game code and the Python API. This document outlines how these updates currently work based on the existing codebase.

## Status Updates

### Triggers
Status updates are initiated from:
1. GameStateService's RunService.Stepped connection
2. NPCManagerV3's updateNPCStatus function
3. Location/action changes in the game

### Flow
1. GameStateService maintains a real-time state cache:
```lua
local gameState = {
    clusters = {},
    events = {},
    humanContext = {},  -- Detailed info about all humans (NPCs and players)
    lastUpdate = 0,
    lastApiSync = 0
}
```

2. NPCManagerV3 formats status updates:
```lua
function NPCManagerV3:updateNPCStatus(npc, updates)
    local locationString = updates.location or "unknown location"
    
    -- Format first-person description based on state
    local descriptions = {
        Idle = string.format("I'm at %s, taking in the surroundings", locationString),
        Interacting = string.format("I'm chatting with visitors at %s", locationString),
        Moving = string.format("I'm walking around %s", locationString),
        -- ...
    }

    local statusBlock = {
        current_location = updates.location or "unknown",
        state = updates.current_action or "Idle",
        description = descriptions[updates.current_action or "Idle"] or descriptions.Idle
    }

    self.ApiService:updateStatusBlock(npc.agentId, statusBlock)
end
```

## Group Updates

### Triggers
Group updates occur when:
1. Players enter/leave interaction range
2. Clusters change (managed by InteractionService)
3. Direct group member updates via NPCManagerV3

### Flow
1. NPCManagerV3 handles group member updates:
```lua
function NPCManagerV3:updateGroupMember(npc, player, isPresent)
    local memberData = {
        entity_id = tostring(player.UserId),
        name = player.Name,
        is_present = isPresent,
        health = "healthy",
        appearance = player.description or "Unknown appearance",
        last_seen = os.date("!%Y-%m-%dT%H:%M:%SZ")
    }

    self.ApiService:upsertGroupMember(npc.agentId, memberData)
end
```

2. GameStateService tracks cluster membership:
```lua
function GameStateService:updateHumanContext(cluster)
    for _, member in ipairs(cluster.members) do
        -- Update position and health data
        local positionData = self:getEntityPosition(member)
        local healthData = self:getEntityHealth(member)
        
        -- Update group membership
        gameState.humanContext[member].currentGroups = {
            members = cluster.members,
            npcs = cluster.npcs,
            players = cluster.players,
            formed = timestamp
        }
    end
end
```

## API Endpoints
The Letta API exposes two main endpoints for these updates:
```lua
ENDPOINTS = {
    GROUP_UPDATE = "/letta/v1/npc/group/update",
    STATUS_UPDATE = "/letta/v1/npc/status/update"
}
```

## Current Limitations
1. Individual API calls per update rather than batching
2. Separate status/group update calls that could potentially be combined
3. Backend sync in GameStateService is currently disabled
4. No explicit rate limiting or debouncing of updates

## Configuration
Update intervals are configured in GameConfig:
```lua
local CONFIG = GameConfig.StateSync
-- UPDATE_INTERVAL: Local state update frequency
-- API_SYNC_INTERVAL: Backend sync frequency
```

## Note
This documentation covers only the functionality visible in the examined code. Additional systems or interactions may exist in other parts of the codebase. 