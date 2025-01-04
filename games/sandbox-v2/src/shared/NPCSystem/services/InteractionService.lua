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
    -- Use cluster data to determine if conversation should end
    local cluster1 = self:getClusterForEntity(npc1.displayName)
    if not cluster1 or not table.find(cluster1.members, npc2.displayName) then
        LoggerService:info("INTERACTION", string.format(
            "Ending conversation - NPCs no longer in same cluster (%s <-> %s)",
            npc1.displayName, npc2.displayName
        ))
        return true
    end
    return false
end

function InteractionService:canInteract(npc1, npc2)
    -- First check if they're in the same cluster
    local cluster1 = self:getClusterForEntity(npc1.displayName)
    if not cluster1 or not table.find(cluster1.members, npc2.displayName) then
        LoggerService:debug("INTERACTION", string.format(
            "Cannot interact - NPCs not in same cluster:\n" ..
            "- %s and %s are too far apart",
            npc1.displayName, npc2.displayName
        ))
        return false
    end
    
    -- Check if either NPC is already in conversation
    if npc1.inConversation or npc2.inConversation then
        LoggerService:debug("INTERACTION", string.format(
            "Cannot interact - NPCs in conversation:\n" ..
            "- %s: inConversation=%s\n" ..
            "- %s: inConversation=%s",
            npc1.displayName, tostring(npc1.inConversation),
            npc2.displayName, tostring(npc2.inConversation)
        ))
        return false
    end
    
    -- Check abilities
    if not npc1.abilities or not npc2.abilities then
        LoggerService:debug("INTERACTION", string.format(
            "Cannot interact - Missing abilities:\n" ..
            "- %s: %s\n" ..
            "- %s: %s",
            npc1.displayName, tostring(npc1.abilities ~= nil),
            npc2.displayName, tostring(npc2.abilities ~= nil)
        ))
        return false
    end
    
    -- Check if they can chat
    if not (table.find(npc1.abilities, "chat") and table.find(npc2.abilities, "chat")) then
        LoggerService:debug("INTERACTION", string.format(
            "Cannot interact - Missing chat ability:\n" ..
            "- %s: %s\n" ..
            "- %s: %s",
            npc1.displayName, tostring(table.find(npc1.abilities, "chat") ~= nil),
            npc2.displayName, tostring(table.find(npc2.abilities, "chat") ~= nil)
        ))
        return false
    end
    
    return true
end

function InteractionService:lockNPCsForInteraction(npc1, npc2)
    npc1.inConversation = true
    npc2.inConversation = true
    npc1.movementState = "locked"
    npc2.movementState = "locked"
    LoggerService:debug("INTERACTION", string.format(
        "Locked NPCs for interaction:\n" ..
        "- %s: inConversation=%s, movementState=%s\n" ..
        "- %s: inConversation=%s, movementState=%s",
        npc1.displayName, tostring(npc1.inConversation), npc1.movementState,
        npc2.displayName, tostring(npc2.inConversation), npc2.movementState
    ))
end

function InteractionService:unlockNPCsAfterInteraction(npc1, npc2)
    LoggerService:debug("INTERACTION", string.format(
        "Unlocking NPCs (before):\n" ..
        "- %s: inConversation=%s, movementState=%s\n" ..
        "- %s: inConversation=%s, movementState=%s",
        npc1.displayName, tostring(npc1.inConversation), npc1.movementState,
        npc2.displayName, tostring(npc2.inConversation), npc2.movementState
    ))

    npc1.inConversation = false
    npc2.inConversation = false
    npc1.movementState = "free"
    npc2.movementState = "free"

    LoggerService:debug("INTERACTION", string.format(
        "Unlocking NPCs (after):\n" ..
        "- %s: inConversation=%s, movementState=%s\n" ..
        "- %s: inConversation=%s, movementState=%s",
        npc1.displayName, tostring(npc1.inConversation), npc1.movementState,
        npc2.displayName, tostring(npc2.inConversation), npc2.movementState
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
    for _, newCluster in ipairs(newClusters) do
        -- Find matching old cluster
        local oldCluster = nil
        for _, old in ipairs(oldClusters) do
            if #old.members == #newCluster.members then
                -- Check if members match
                local matches = true
                for _, member in ipairs(old.members) do
                    if not table.find(newCluster.members, member) then
                        matches = false
                        break
                    end
                end
                if matches then
                    oldCluster = old
                    break
                end
            end
        end

        -- If cluster composition changed, notify members
        if not oldCluster then
            for _, memberName in ipairs(newCluster.members) do
                -- Notify this member about their new cluster mates
                -- This would replace the current "NPC entered area" messages
            end
        end
    end
end

function InteractionService:getLatestClusters()
    return lastClusters or {}  -- Return cached clusters
end

return InteractionService 