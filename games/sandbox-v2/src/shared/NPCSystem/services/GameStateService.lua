local GameStateService = {}

local HttpService = game:GetService("HttpService")
local LoggerService = require(script.Parent.LoggerService)
local GameConfig = require(script.Parent.Parent.config.GameConfig)
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

-- Use config from GameConfig
local CONFIG = GameConfig.StateSync

LoggerService:info("SNAPSHOT", string.format(
    "Using sync intervals - Local: %ds, Backend: %ds",
    CONFIG.UPDATE_INTERVAL,
    CONFIG.API_SYNC_INTERVAL
))

-- Add constants at the top
local MOVEMENT_THRESHOLD = 0.1 -- Only log movements greater than 0.1 studs
local RunService = game:GetService("RunService")
local activeSyncCount = 0  -- Track concurrent syncs
local MAX_CONCURRENT_SYNCS = 1
local SYNC_CHECK_INTERVAL = 1 -- Only check sync every second

local lastSyncCheck = 0

-- At the top, add debug logging for time checks
local function debugTimeDiff(label, current, last, interval)
    LoggerService:debug("TIMING", string.format(
        "%s check: now=%d, last=%d, diff=%d, interval=%d",
        label,
        current,
        last,
        current - last,
        interval
    ))
end

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
        CONFIG.UPDATE_INTERVAL = config.snapshotInterval  -- Match local updates to sync
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
                state = humanoid:GetState().Name,
                isMoving = humanoid.MoveDirection.Magnitude > 0.1,
                velocity = humanoid.MoveDirection.Magnitude * humanoid.WalkSpeed
            }
        end
    end
    
    -- Return default health if not found
    return {
        current = 100,
        max = 100,
        state = "Unknown",
        isMoving = false
    }
end

function GameStateService:hasPositionChanged(oldPos, newPos)
    if not oldPos or not newPos then return false end
    
    return math.abs(oldPos.x - newPos.x) > CONFIG.MOVEMENT_THRESHOLD or
           math.abs(oldPos.y - newPos.y) > CONFIG.MOVEMENT_THRESHOLD or
           math.abs(oldPos.z - newPos.z) > CONFIG.MOVEMENT_THRESHOLD
end

function GameStateService:updateHumanContext(cluster)
    for _, member in ipairs(cluster.members) do
        local positionData = self:getEntityPosition(member)
        local healthData = self:getEntityHealth(member)
        local timestamp = os.time()
        
        if not gameState.humanContext[member] then
            gameState.humanContext[member] = {
                position = positionData,
                health = healthData,
                lastSeen = timestamp,
                positionTimestamp = timestamp,
                stateTimestamp = timestamp,
                currentGroups = {}
            }
        else
            local existing = gameState.humanContext[member]
            existing.position = positionData
            existing.health = healthData
            existing.lastSeen = timestamp
            -- Update timestamps only when values change
            if self:hasPositionChanged(existing.position, positionData) then
                existing.positionTimestamp = timestamp
            end
            if existing.health.state ~= healthData.state then
                existing.stateTimestamp = timestamp
            end
        end
        
        gameState.humanContext[member].currentGroups = {
            members = cluster.members,
            npcs = cluster.npcs,
            players = cluster.players,
            formed = timestamp
        }
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

function GameStateService:getSnapshot()
    -- Build clusters
    local npcClusters = {}
    for _, cluster in ipairs(gameState.clusters) do
        if cluster.npcs > 0 then
            table.insert(npcClusters, cluster)
        end
    end

    return {
        timestamp = os.time(),
        clusters = npcClusters,
        events = gameState.events,
        humanContext = gameState.humanContext
    }
end

-- Modify the sync function to disable automatic syncing
function GameStateService:syncWithBackend()
    -- Disable automatic syncing for now
    return false
    
    -- Rest of existing sync code...
end

-- Initialize heartbeat
RunService.Stepped:Connect(function()
    local now = os.time()
    
    -- Only check sync status periodically to reduce spam
    if now - lastSyncCheck < SYNC_CHECK_INTERVAL then
        return
    end
    lastSyncCheck = now
    
    -- Update local state first
    if now - gameState.lastUpdate >= CONFIG.UPDATE_INTERVAL then
        local clusters = InteractionService:getLatestClusters()
        if not clusters then
            LoggerService:warn("SNAPSHOT", "No clusters returned from InteractionService")
            return
        end
        
        gameState.clusters = clusters
        gameState.lastUpdate = now
        
        -- Update human context for each cluster
        for _, cluster in ipairs(clusters) do
            GameStateService:updateHumanContext(cluster)
        end
    end
    
    -- Remove backend sync check entirely
    -- if now - gameState.lastApiSync >= CONFIG.API_SYNC_INTERVAL ... 
end)

LoggerService:info("SYSTEM", "GameStateService heartbeat initialized")

function GameStateService:hasEntityMoved(oldPos, newPos)
    if not oldPos or not newPos then return false end
    
    local xDiff = math.abs(oldPos.X - newPos.X)
    local yDiff = math.abs(oldPos.Y - newPos.Y)
    local zDiff = math.abs(oldPos.Z - newPos.Z)
    
    return xDiff > CONFIG.MOVEMENT_THRESHOLD or 
           yDiff > CONFIG.MOVEMENT_THRESHOLD or 
           zDiff > CONFIG.MOVEMENT_THRESHOLD
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