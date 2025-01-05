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

function GameStateService:updateHumanContext(cluster)
    for _, member in ipairs(cluster.members) do
        if not gameState.humanContext[member] then
            gameState.humanContext[member] = {
                relationships = {},
                currentGroups = {},
                recentInteractions = {},
                lastSeen = os.time()
            }
        end
        
        -- Update group membership
        gameState.humanContext[member].currentGroups = {
            primary = member,
            members = cluster.members,
            npcs = cluster.npcs,
            players = cluster.players,
            formed = os.time()
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

-- Sync with backend
function GameStateService:syncWithBackend()
    LoggerService:debug("SNAPSHOT", "Starting syncWithBackend...")
    -- Filter clusters to only include those with NPCs
    local npcClusters = {}
    for _, cluster in ipairs(gameState.clusters) do
        if cluster.npcs > 0 then
            table.insert(npcClusters, cluster)
        end
    end
    LoggerService:debug("SNAPSHOT", string.format(
        "Filtered %d clusters down to %d NPC-containing clusters",
        #gameState.clusters, #npcClusters
    ))
    
    local payload = {
        clusters = npcClusters,
        events = gameState.events,
        humanContext = gameState.humanContext,
        timestamp = os.time()
    }
    
    LoggerService:debug("SNAPSHOT", string.format("Payload prepared with %d clusters, %d events", 
        #gameState.clusters, #gameState.events))
    
    -- Send to Letta snapshot endpoint
    local success, response = pcall(function()
        local url = LettaConfig.BASE_URL .. LettaConfig.ENDPOINTS.SNAPSHOT
        LoggerService:debug("SNAPSHOT", "Sending to URL: " .. url)
        
        -- Add headers
        local headers = {
            ["Content-Type"] = "application/json",
            ["Accept"] = "application/json"
        }
        
        local jsonPayload = HttpService:JSONEncode(payload)
        LoggerService:debug("SNAPSHOT", "Sending payload: " .. jsonPayload)
        
        return HttpService:RequestAsync({
            Url = url,
            Method = "POST",
            Headers = headers,
            Body = jsonPayload
        })
    end)
    
    if success then
        LoggerService:debug("SNAPSHOT", "Successfully sent game snapshot to backend")
        LoggerService:debug("SNAPSHOT", "Response: " .. HttpService:JSONEncode(response))
    else
        LoggerService:error("SNAPSHOT", "Failed to send snapshot: " .. tostring(response))
        LoggerService:error("SNAPSHOT", "Error details: " .. debug.traceback())
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
        LoggerService:debug("SNAPSHOT", "Time to sync with backend...")
        task.spawn(function()
            GameStateService:syncWithBackend()
        end)
        gameState.lastApiSync = now
    end
end)

LoggerService:info("SYSTEM", "GameStateService heartbeat initialized")

return GameStateService 