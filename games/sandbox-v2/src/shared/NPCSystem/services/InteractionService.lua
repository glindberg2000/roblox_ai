-- InteractionService.lua
local InteractionService = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local LoggerService = require(NPCSystem.services.LoggerService)

-- Store the last calculated clusters
local lastClusters = {}
local lastUpdateTime = 0
local CLUSTER_UPDATE_INTERVAL = 1 -- Update clusters every second

function InteractionService:checkRangeAndEndConversation(npc1, npc2)
    -- Only check cluster membership without range messages
    local cluster1 = self:getClusterForEntity(npc1.displayName)
    if not cluster1 or not table.find(cluster1.members, npc2.displayName) then
        LoggerService:debug("CLUSTER", string.format(
            "NPCs in different clusters: %s, %s",
            npc1.displayName, npc2.displayName
        ))
        return true
    end
    return false
end

function InteractionService:canInteract(npc1, npc2)
    -- Only check cluster membership for proximity awareness
    local cluster1 = self:getClusterForEntity(npc1.displayName)
    if not cluster1 or not table.find(cluster1.members, npc2.displayName) then
        LoggerService:debug("CLUSTER", string.format(
            "NPCs in different clusters: %s, %s",
            npc1.displayName, npc2.displayName
        ))
        return false
    end
    
    -- Remove all other checks - let backend handle them
    return true
end

function InteractionService:lockNPCsForInteraction(npc1, npc2)
    -- Remove movement locking but keep conversation state
    npc1.inConversation = true
    npc2.inConversation = true
    LoggerService:debug("INTERACTION", string.format(
        "Started conversation between:\n" ..
        "- %s\n" ..
        "- %s",
        npc1.displayName,
        npc2.displayName
    ))
end

function InteractionService:unlockNPCsAfterInteraction(npc1, npc2)
    -- Remove movement unlocking but keep conversation cleanup
    npc1.inConversation = false
    npc2.inConversation = false
    LoggerService:debug("INTERACTION", string.format(
        "Ended conversation between:\n" ..
        "- %s\n" ..
        "- %s",
        npc1.displayName,
        npc2.displayName
    ))
end

function InteractionService:getClusterForEntity(entityName)
    -- Return cached cluster info if recent enough
    if os.time() - lastUpdateTime < CLUSTER_UPDATE_INTERVAL then
        for _, cluster in ipairs(lastClusters) do
            if table.find(cluster.members, entityName) then
                return cluster
            end
        end
    end
    return nil
end

function InteractionService:checkProximity(npc1, npc2)
    -- Use cluster data instead of direct distance check
    local cluster1 = self:getClusterForEntity(npc1.displayName)
    if cluster1 then
        return table.find(cluster1.members, npc2.displayName) ~= nil
    end
    
    return false
end

function InteractionService:logProximityMatrix(npcs)
    local matrix = {}
    local positions = {}
    
    -- First collect all positions including NPCs and Players
    for _, npc in pairs(npcs) do
        if npc.model and npc.model.PrimaryPart then
            local pos = npc.model.PrimaryPart.Position
            positions[npc.displayName] = {
                x = pos.X,
                y = pos.Y,
                z = pos.Z,
                type = "npc"
            }
        end
    end
    
    -- Add players to positions
    for _, player in ipairs(game:GetService("Players"):GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local pos = player.Character.HumanoidRootPart.Position
            positions[player.Name] = {
                x = pos.X,
                y = pos.Y,
                z = pos.Z,
                type = "player"
            }
        end
    end
    
    -- Build distance matrix including player distances
    for name1, pos1 in pairs(positions) do
        matrix[name1] = {}
        for name2, pos2 in pairs(positions) do
            if name1 ~= name2 then
                local dx = pos1.x - pos2.x
                local dy = pos1.y - pos2.y
                local dz = pos1.z - pos2.z
                local distance = (dx * dx + dy * dy + dz * dz) ^ 0.5
                matrix[name1][name2] = distance
            end
        end
    end
    
    -- Log the matrix
    local output = "NPC Proximity Matrix:\n\n"
    
    -- Log positions first, now with type indicators
    output = output .. "Positions:\n"
    for name, pos in pairs(positions) do
        output = output .. string.format("- %s [%s]: (%.1f, %.1f, %.1f)\n", 
            name, pos.type, pos.x, pos.y, pos.z)
    end
    
    -- Log distance matrix
    output = output .. "\nDistances:\n"
    for name1, distances in pairs(matrix) do
        for name2, dist in pairs(distances) do
            output = output .. string.format("- %s <-> %s: %.1f\n",
                name1, name2, dist)
        end
    end
    
    -- Analyze clusters (now including players)
    local clusters = {}
    local clusterThreshold = 10
    
    for name1, pos1 in pairs(positions) do
        local foundCluster = false
        for i, cluster in ipairs(clusters) do
            for _, memberName in ipairs(cluster.members) do
                if matrix[name1][memberName] <= clusterThreshold then
                    table.insert(cluster.members, name1)
                    cluster.npcs = cluster.npcs + (pos1.type == "npc" and 1 or 0)
                    cluster.players = cluster.players + (pos1.type == "player" and 1 or 0)
                    foundCluster = true
                    break
                end
            end
            if foundCluster then break end
        end
        
        if not foundCluster then
            table.insert(clusters, {
                members = {name1},
                npcs = pos1.type == "npc" and 1 or 0,
                players = pos1.type == "player" and 1 or 0
            })
        end
    end
    
    -- Log enhanced cluster information
    output = output .. "\nClusters (within " .. clusterThreshold .. " studs):\n"
    for i, cluster in ipairs(clusters) do
        output = output .. string.format("Cluster %d (%d NPCs, %d Players): %s\n",
            i, cluster.npcs, cluster.players,
            table.concat(cluster.members, ", "))
    end
    
    -- Store clusters for later use
    lastClusters = clusters
    lastUpdateTime = os.time()
    
    LoggerService:debug("PROXIMITY_MATRIX", output)
end

function InteractionService:handleClusterChanges(oldClusters, newClusters)
    -- Just track cluster changes without sending notifications
    for _, newCluster in ipairs(newClusters) do
        LoggerService:debug("CLUSTER", string.format(
            "Cluster updated: %d members (%s)",
            #newCluster.members,
            table.concat(newCluster.members, ", ")
        ))
    end
end

function InteractionService:getLatestClusters()
    return lastClusters or {}  -- Return cached clusters
end

function InteractionService:calculateClusters()
    LoggerService:debug("CLUSTER", "Starting cluster calculation")
    local npcPositions = {}
    
    -- Get positions from NPC manager
    for npcId, npc in pairs(self.npcManager.npcs) do
        if npc.rootPart then
            npcPositions[npcId] = npc.rootPart.Position
            LoggerService:debug("CLUSTER_CALC", string.format(
                "NPC %s (%s) position: %s",
                npcId,
                npc.displayName,
                tostring(npc.rootPart.Position)
            ))
        else
            LoggerService:warn("CLUSTER", "Missing rootPart for "..npcId)
        end
    end

    -- Cluster calculation
    local clusters = {}
    local CLUSTER_RADIUS = 20
    local clusterMap = {}

    for npcId1, pos1 in pairs(npcPositions) do
        local clusterMembers = {npcId1}
        
        for npcId2, pos2 in pairs(npcPositions) do
            if npcId1 ~= npcId2 and (pos1 - pos2).Magnitude <= CLUSTER_RADIUS then
                table.insert(clusterMembers, npcId2)
                LoggerService:debug("CLUSTER_CALC", string.format(
                    "%s is within %d studs of %s",
                    self.npcManager.npcs[npcId2].displayName,
                    CLUSTER_RADIUS,
                    self.npcManager.npcs[npcId1].displayName
                ))
            end
        end
        
        table.sort(clusterMembers)
        local clusterKey = table.concat(clusterMembers, "|")
        
        if not clusterMap[clusterKey] then
            clusterMap[clusterKey] = {
                members = clusterMembers,
                center = pos1
            }
            LoggerService:info("CLUSTER_FORMED", string.format(
                "New cluster: %s (%d members)",
                clusterKey,
                #clusterMembers
            ))
        end
    end

    return getMapValues(clusterMap)
end

function InteractionService:updateProximityMatrix()
    local newClusters = self:calculateClusters()
    
    LoggerService:debug("CLUSTER_UPDATE", string.format(
        "Cluster state update - Total clusters: %d",
        #newClusters
    ))
    
    -- Store clusters with timestamps
    lastClusters = newClusters
    lastUpdateTime = os.time()
    
    -- Log full cluster details
    for i, cluster in ipairs(newClusters) do
        LoggerService:info("CLUSTER_DETAIL", string.format(
            "Cluster %d: %s @ %s",
            i,
            table.concat(cluster.members, ", "),
            tostring(cluster.center)
        ))
    end
    
    self:handleClusterChanges(lastClusters, newClusters)
end

function InteractionService.new(npcManager)
    local self = {}
    self.npcManager = npcManager
    
    LoggerService:debug("CLUSTER", "Creating new InteractionService instance")
    
    -- Initialize cluster detection
    task.spawn(function()
        LoggerService:debug("CLUSTER", "Starting cluster detection loop")
        while true do
            if self.npcManager and self.npcManager.initializationComplete then
                LoggerService:debug("CLUSTER", "Running cluster detection cycle")
                self:updateProximityMatrix()
            else
                LoggerService:debug("CLUSTER", "Waiting for NPC initialization to complete...")
            end
            task.wait(2) -- Check clusters every 2 seconds
        end
    end)
    
    return setmetatable(self, {__index = InteractionService})
end

return InteractionService 