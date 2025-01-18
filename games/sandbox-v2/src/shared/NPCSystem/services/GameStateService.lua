local GameStateService = {}

local HttpService = game:GetService("HttpService")
local LoggerService = require(script.Parent.LoggerService)
local LettaConfig = require(script.Parent.Parent.config.LettaConfig)
local InteractionService = require(script.Parent.InteractionService)

LoggerService:info("SNAPSHOT", "Loading GameStateService module...")
LoggerService:info("SNAPSHOT", "Initializing GameStateService...")

-- Real-time state cache
local gameState = {
    clusters = {},
    events = {},
    humanContext = {},  -- Detailed info about all humans (NPCs and players)
    lastUpdate = 0,
    lastApiSync = 0
}

LoggerService:debug("SNAPSHOT", "Game state cache initialized")

-- Configuration
local CONFIG = {
    UPDATE_INTERVAL = 1,    -- Local state update (seconds)
    API_SYNC_INTERVAL = 5,  -- Backend sync interval (seconds)
    CACHE_EXPIRY = 30      -- How long to keep stale data
}

LoggerService:info("SNAPSHOT", "Setting up heartbeat...")

-- Add constants at the top
local MOVEMENT_THRESHOLD = 0.1 -- Only log movements greater than 0.1 studs

function GameStateService.init(config)
    if not config then
        config = {
            enableBackendSync = true,
            snapshotInterval = CONFIG.API_SYNC_INTERVAL
        }
    end
    
    -- Update config if provided
    if config.snapshotInterval then
        CONFIG.API_SYNC_INTERVAL = config.snapshotInterval
    end
    
    -- Initialize state
    gameState = {
        clusters = {},
        events = {},
        humanContext = {},
        lastUpdate = 0,
        lastApiSync = 0
    }
    
    LoggerService:debug("SNAPSHOT", "GameStateService initialized with config:", config)
    return true
end

function GameStateService:getEntityPosition(member)
    -- Try multiple ways to find the character
    local character = game.Workspace:FindFirstChild(member)
    if not character then
        local npcFolder = game.Workspace:FindFirstChild("NPCs")
        if npcFolder then
            character = npcFolder:FindFirstChild(member)
        end
        
        if not character then
            local Players = game:GetService("Players")
            local player = Players:FindFirstChild(member)
            if player then
                character = player.Character
            end
        end
    end
    
    if character then
        local success, position = pcall(function()
            return character:GetPivot().Position
        end)
        
        if success then
            return {
                x = position.X,
                y = position.Y,
                z = position.Z
            }
        end
    end
    
    -- Return last known position or default
    local existing = gameState.humanContext[member]
    return existing and existing.position or {x = 0, y = 0, z = 0}
end

function GameStateService:getEntityHealth(member)
    -- Try multiple ways to find the character
    local character = game.Workspace:FindFirstChild(member)
    if not character then
        local npcFolder = game.Workspace:FindFirstChild("NPCs")
        if npcFolder then
            character = npcFolder:FindFirstChild(member)
        end
    end
    
    if character then
        local humanoid = character:FindFirstChild("Humanoid")
        if humanoid then
            return {
                current = humanoid.Health,
                max = humanoid.MaxHealth,
                state = humanoid:GetState().Name
            }
        end
    end
    
    -- Return default health if not found
    return {
        current = 100,
        max = 100,
        state = "Unknown"
    }
end

function GameStateService:hasPositionChanged(oldPos, newPos)
    if not oldPos or not newPos then return false end
    
    -- Check if positions are actually different
    return math.abs(oldPos.x - newPos.x) > MOVEMENT_THRESHOLD or
           math.abs(oldPos.y - newPos.y) > MOVEMENT_THRESHOLD or
           math.abs(oldPos.z - newPos.z) > MOVEMENT_THRESHOLD
end

function GameStateService:updateHumanContext(cluster)
    -- Track changes for efficient logging
    local changes = {}
    
    for _, member in ipairs(cluster.members) do
        local positionData = self:getEntityPosition(member)
        local healthData = self:getEntityHealth(member)
        local location = "Unknown"
        
        -- Only log position/health changes
        local existing = gameState.humanContext[member]
        local positionChanged = existing and self:hasPositionChanged(existing.position, positionData)
        local healthChanged = existing and (
            existing.health.current ~= healthData.current or
            existing.health.state ~= healthData.state
        )
        
        if not existing or positionChanged or healthChanged then
            changes[member] = {
                old = existing and {
                    position = existing.position,
                    health = existing.health
                },
                new = {
                    position = positionData,
                    health = healthData
                }
            }
        end
        
        -- Update context
        if not existing then
            gameState.humanContext[member] = {
                relationships = {},
                currentGroups = {},
                recentInteractions = {},
                lastSeen = os.time(),
                location = location,
                position = positionData,
                health = healthData
            }
        else
            existing.location = location
            existing.position = positionData
            existing.health = healthData
            existing.lastSeen = os.time()
        end
        
        -- Update group membership
        gameState.humanContext[member].currentGroups = {
            members = cluster.members,
            npcs = cluster.npcs,
            players = cluster.players,
            formed = os.time()
        }
    end
    
    -- Log changes in batch
    if next(changes) and LoggerService.isDebugEnabled then
        LoggerService:debug("SNAPSHOT", "\n=== Entity Updates ===")
        for entity, change in pairs(changes) do
            if change.old then
                -- Log position changes
                if change.old.position then
                    LoggerService:debug("SNAPSHOT", string.format(
                        "%s moved: (%.1f, %.1f, %.1f) -> (%.1f, %.1f, %.1f)",
                        entity,
                        change.old.position.x, change.old.position.y, change.old.position.z,
                        change.new.position.x, change.new.position.y, change.new.position.z
                    ))
                end
                
                -- Log health changes
                if change.old.health then
                    LoggerService:debug("SNAPSHOT", string.format(
                        "%s health: %d/%d [%s] -> %d/%d [%s]",
                        entity,
                        change.old.health.current, change.old.health.max, change.old.health.state,
                        change.new.health.current, change.new.health.max, change.new.health.state
                    ))
                end
            else
                LoggerService:debug("SNAPSHOT", string.format(
                    "%s appeared: (%.1f, %.1f, %.1f) [Health: %d/%d %s]",
                    entity,
                    change.new.position.x, change.new.position.y, change.new.position.z,
                    change.new.health.current, change.new.health.max, change.new.health.state
                ))
            end
        end
        LoggerService:debug("SNAPSHOT", "=======================\n")
    end
end

function GameStateService:recordEvent(eventType, data)
    table.insert(gameState.events, {
        type = eventType,
        data = data,
        timestamp = os.time()
    })
end

function GameStateService:getContextForNPC(npcName)
    return {
        selfContext = gameState.humanContext[npcName],
        currentCluster = self:getCurrentCluster(npcName),
        nearbyGroups = self:getNearbyGroups(npcName),
        recentEvents = self:getRelevantEvents(npcName)
    }
end

-- Sync with backend
function GameStateService:syncWithBackend()
    LoggerService:info("SNAPSHOT", "Starting backend sync...")
    
    -- Build clusters
    local npcClusters = {}
    for _, cluster in ipairs(gameState.clusters) do
        if cluster.npcs > 0 then
            table.insert(npcClusters, cluster)
        end
    end
    
    -- Only log detailed positions in debug mode
    if LoggerService.isDebugEnabled then
        LoggerService:info("SNAPSHOT", "\n=== Entity Groups & Positions ===")
        
        -- Group entities by cluster for cleaner logging
        local clusterGroups = {}
        for name, context in pairs(gameState.humanContext) do
            local groupId = context.currentGroups.formed or 0
            clusterGroups[groupId] = clusterGroups[groupId] or {}
            table.insert(clusterGroups[groupId], {
                name = name,
                pos = context.position,
                health = context.health,
                isPlayer = context.currentGroups.players and context.currentGroups.players > 0
            })
        end
        
        -- Log each cluster group
        for groupId, members in pairs(clusterGroups) do
            LoggerService:info("SNAPSHOT", string.format(
                "\nGroup %d:", 
                groupId
            ))
            for _, member in ipairs(members) do
                local pos = member.pos
                local health = member.health
                LoggerService:info("SNAPSHOT", string.format(
                    "  %s%s: (%.1f, %.1f, %.1f) [Health: %d/%d %s]",
                    member.name,
                    member.isPlayer and " [PLAYER]" or "",
                    pos.x, pos.y, pos.z,
                    health.current, health.max, health.state
                ))
            end
        end
        LoggerService:info("SNAPSHOT", "\n===========================")
    end

    local payload = {
        timestamp = os.time(),
        clusters = npcClusters,
        events = gameState.events,
        humanContext = gameState.humanContext
    }
    
    -- Log attempt with detailed summary
    local totalPlayers = 0
    local totalNPCs = 0
    for _, cluster in ipairs(npcClusters) do
        totalPlayers = totalPlayers + cluster.players
        totalNPCs = totalNPCs + cluster.npcs
    end
    
    LoggerService:info("SNAPSHOT", string.format(
        "Sending snapshot: %d clusters (%d players, %d NPCs)",
        #npcClusters,
        totalPlayers,
        totalNPCs
    ))
    
    -- Send to Letta snapshot endpoint
    local success, response = pcall(function()
        local url = LettaConfig.BASE_URL .. LettaConfig.ENDPOINTS.SNAPSHOT
        
        -- Add headers
        local headers = {
            ["Content-Type"] = "application/json",
            ["Accept"] = "application/json"
        }
        
        local jsonPayload = HttpService:JSONEncode(payload)
        
        LoggerService:debug("SNAPSHOT", "Sending request...")
        
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = headers,
            Body = jsonPayload
        })
    end)
    
    if success then
        if response.Success then
            LoggerService:info("SNAPSHOT", "Successfully sent snapshot")
            LoggerService:debug("SNAPSHOT", "Response: " .. HttpService:JSONEncode(response))
        else
            LoggerService:error("SNAPSHOT", "API Error: " .. tostring(response.StatusMessage))
            LoggerService:debug("SNAPSHOT", "Full response: " .. HttpService:JSONEncode(response))
        end
    else
        LoggerService:error("SNAPSHOT", "Failed to send snapshot: " .. tostring(response))
    end
    
    return success
end

-- Initialize heartbeat
game:GetService("RunService").Heartbeat:Connect(function()
    local now = os.time()
    
    -- Update local state
    if now - gameState.lastUpdate >= CONFIG.UPDATE_INTERVAL then
        LoggerService:debug("SNAPSHOT", "Heartbeat: Updating local state...")
        local clusters = InteractionService:getLatestClusters()
        if not clusters then
            LoggerService:warn("SNAPSHOT", "No clusters returned from InteractionService")
            return
        end
        gameState.clusters = clusters
        
        LoggerService:debug("SNAPSHOT", string.format("Got %d clusters", #clusters))
        
        -- Update human context for each cluster
        for _, cluster in ipairs(clusters) do
            GameStateService:updateHumanContext(cluster)
        end
        
        gameState.lastUpdate = now
    end
    
    -- Sync with backend
    if now - gameState.lastApiSync >= CONFIG.API_SYNC_INTERVAL then
        LoggerService:info("SNAPSHOT", "Time to sync with backend...")
        task.spawn(function()
            local success = GameStateService:syncWithBackend()
            if not success then
                LoggerService:error("SNAPSHOT", "Backend sync failed")
            end
        end)
        gameState.lastApiSync = now
    end
end)

LoggerService:info("SYSTEM", "GameStateService heartbeat initialized")

function GameStateService:hasEntityMoved(oldPos, newPos)
    if not oldPos or not newPos then return false end
    
    local xDiff = math.abs(oldPos.X - newPos.X)
    local yDiff = math.abs(oldPos.Y - newPos.Y)
    local zDiff = math.abs(oldPos.Z - newPos.Z)
    
    return xDiff > MOVEMENT_THRESHOLD or 
           yDiff > MOVEMENT_THRESHOLD or 
           zDiff > MOVEMENT_THRESHOLD
end

function GameStateService:compareEntityStates(oldState, newState)
    local changes = {}
    
    if self:hasEntityMoved(oldState.position, newState.position) then
        changes.moved = {
            from = oldState.position,
            to = newState.position
        }
    end
    
    -- Rest of comparison logic...
    
    return changes
end

return GameStateService 