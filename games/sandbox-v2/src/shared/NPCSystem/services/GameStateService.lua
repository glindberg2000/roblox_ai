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
    -- Only log workspace contents once at startup
    if not self.workspaceLogged then
        LoggerService:debug("SNAPSHOT", "[Position] ===== Workspace Contents =====")
        for _, child in ipairs(game.Workspace:GetChildren()) do
            if child:IsA("Model") or child:IsA("Folder") then
                LoggerService:debug("SNAPSHOT", string.format("[Position] %s (%s)", 
                    child.Name, child.ClassName))
            end
        end
        LoggerService:debug("SNAPSHOT", "[Position] =============================")
        self.workspaceLogged = true
    end

    for _, member in ipairs(cluster.members) do
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
        
        local location = "Unknown"
        local positionData = nil
        
        if character then
            local success, position = pcall(function()
                return character:GetPivot().Position
            end)
            
            if success then
                -- Only log when we successfully get a position
                LoggerService:info("SNAPSHOT", string.format("[Position] %s at: %.1f, %.1f, %.1f",
                    member, position.X, position.Y, position.Z))
                
                -- Store position in consistent format
                positionData = {
                    x = position.X,
                    y = position.Y,
                    z = position.Z
                }
                location = "Unknown"  -- Named location can be added later
            end
        end
        
        -- Create or update context
        local contextData = {
            relationships = {},
            currentGroups = {},
            recentInteractions = {},
            lastSeen = os.time(),
            location = location,
            position = positionData
        }
        
        if not gameState.humanContext[member] then
            gameState.humanContext[member] = contextData
        else
            -- Update existing context
            gameState.humanContext[member].location = location
            gameState.humanContext[member].position = positionData
        end
        
        -- Debug log the final context
        LoggerService:debug("SNAPSHOT", string.format("[Position] Pre-sync data for %s: %s",
            member, HttpService:JSONEncode(gameState.humanContext[member])))
        
        -- Update group membership
        gameState.humanContext[member].currentGroups = {
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
    
    -- Remove detailed context logging
    local npcClusters = {}
    for _, cluster in ipairs(gameState.clusters) do
        if cluster.npcs > 0 then
            table.insert(npcClusters, cluster)
        end
    end
    
    local payload = {
        clusters = npcClusters,
        events = gameState.events,
        humanContext = gameState.humanContext,
        timestamp = os.time()
    }
    
    -- Only log summary
    LoggerService:info("SNAPSHOT", string.format("Sending snapshot with %d clusters, %d entities",
        #npcClusters, #gameState.humanContext))
    
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