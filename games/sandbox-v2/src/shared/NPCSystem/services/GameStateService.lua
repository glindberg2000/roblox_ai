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

function GameStateService:updateHumanContext(cluster)
    -- Track changes for efficient logging
    local changes = {}
    
    for _, member in ipairs(cluster.members) do
        local positionData = self:getEntityPosition(member)
        local location = "Unknown"  -- Named location can be added later
        
        -- Only log position changes
        local existing = gameState.humanContext[member]
        if not existing or 
           existing.position.x ~= positionData.x or
           existing.position.y ~= positionData.y or
           existing.position.z ~= positionData.z then
            changes[member] = {
                old = existing and existing.position,
                new = positionData
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
                position = positionData
            }
        else
            existing.location = location
            existing.position = positionData
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
    
    -- Log position changes in batch
    if next(changes) and LoggerService.isDebugEnabled then
        LoggerService:debug("SNAPSHOT", "\n=== Position Updates ===")
        for entity, change in pairs(changes) do
            if change.old then
                LoggerService:debug("SNAPSHOT", string.format(
                    "%s moved: (%.1f, %.1f, %.1f) -> (%.1f, %.1f, %.1f)",
                    entity,
                    change.old.x, change.old.y, change.old.z,
                    change.new.x, change.new.y, change.new.z
                ))
            else
                LoggerService:debug("SNAPSHOT", string.format(
                    "%s appeared at: (%.1f, %.1f, %.1f)",
                    entity,
                    change.new.x, change.new.y, change.new.z
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
        LoggerService:debug("SNAPSHOT", "\n=== Entity Groups & Positions ===")
        
        -- Group entities by cluster for cleaner logging
        local clusterGroups = {}
        for name, context in pairs(gameState.humanContext) do
            local groupId = context.currentGroups.formed or 0
            clusterGroups[groupId] = clusterGroups[groupId] or {}
            table.insert(clusterGroups[groupId], {
                name = name,
                pos = context.position,
                isPlayer = context.currentGroups.players and context.currentGroups.players > 0
            })
        end
        
        -- Log each cluster group
        for groupId, members in pairs(clusterGroups) do
            LoggerService:debug("SNAPSHOT", string.format(
                "\nGroup %d:", 
                groupId
            ))
            for _, member in ipairs(members) do
                local pos = member.pos
                LoggerService:debug("SNAPSHOT", string.format(
                    "  %s%s: (%.1f, %.1f, %.1f)",
                    member.name,
                    member.isPlayer and " [PLAYER]" or "",
                    pos.x, pos.y, pos.z
                ))
            end
        end
        LoggerService:debug("SNAPSHOT", "\n===========================")
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

return GameStateService 