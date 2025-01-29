local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local GameStateService = require(ReplicatedStorage.Shared.NPCSystem.services.GameStateService)
local InteractionService = require(ReplicatedStorage.Shared.NPCSystem.services.InteractionService)

local ClusterSystem = {}

-- Make cluster data accessible to other systems
ClusterSystem.activeClusters = {}
ClusterSystem.clusterMembers = {} -- Quick lookup by entity ID
local CLUSTER_RADIUS = 10

-- Add method to get all active clusters
function ClusterSystem.getAllClusters()
    return ClusterSystem.activeClusters
end

-- Add method to get an entity's cluster ID directly
function ClusterSystem.getEntityClusterId(entityId)
    return ClusterSystem.clusterMembers[entityId]
end

function ClusterSystem.verifyClusterMembership(sourceId, targetId)
    -- Quick lookup using clusterMembers
    local sourceClusterId = ClusterSystem.clusterMembers[sourceId]
    local targetClusterId = ClusterSystem.clusterMembers[targetId]
    
    -- If both entities are in the same cluster
    if sourceClusterId and sourceClusterId == targetClusterId then
        local cluster = ClusterSystem.activeClusters[sourceClusterId]
        if cluster and cluster.positions[sourceId] and cluster.positions[targetId] then
            LoggerService:debug("CLUSTER", string.format(
                "Verified cluster membership for %s and %s in cluster %s",
                sourceId,
                targetId,
                sourceClusterId
            ))
            return true
        end
    end
    
    return false
end

function ClusterSystem.updateClusterState(clusterId, members, positions)
    if not members or #members == 0 then
        LoggerService:warn("CLUSTER", "Attempted to update cluster with no members")
        return
    end
    
    -- Validate position data
    local validPositions = true
    for _, member in ipairs(members) do
        if not positions[member] then
            LoggerService:warn("CLUSTER", string.format(
                "Missing position data for member %s in cluster %s",
                member,
                clusterId
            ))
            validPositions = false
            break
        end
    end
    
    if not validPositions then return end
    
    -- Update main cluster data
    ClusterSystem.activeClusters[clusterId] = {
        members = members,
        positions = positions,
        lastUpdate = os.clock()
    }
    
    -- Update quick lookup table
    for _, member in ipairs(members) do
        ClusterSystem.clusterMembers[member] = clusterId
    end
    
    -- Sync with GameStateService
    GameStateService:recordEvent("cluster_update", {
        clusterId = clusterId,
        members = members,
        positions = positions
    })
    
    -- Broadcast cluster update to interested systems
    if game:GetService("RunService"):IsServer() then
        game:GetService("ReplicatedStorage"):WaitForChild("ClusterUpdateEvent"):FireAllClients(
            clusterId,
            members,
            positions
        )
    end
    
    LoggerService:debug("CLUSTER", string.format(
        "Updated cluster %s with %d members",
        clusterId,
        #members
    ))
end

-- Add method to check if entities can interact
function ClusterSystem.canEntitiesInteract(entity1Id, entity2Id)
    return ClusterSystem.verifyClusterMembership(entity1Id, entity2Id)
end

-- Add cleanup method for removed entities
function ClusterSystem.removeEntity(entityId)
    local clusterId = ClusterSystem.clusterMembers[entityId]
    if clusterId then
        local cluster = ClusterSystem.activeClusters[clusterId]
        if cluster then
            -- Remove from members array
            local index = table.find(cluster.members, entityId)
            if index then
                table.remove(cluster.members, index)
            end
            -- Remove position data
            if cluster.positions[entityId] then
                cluster.positions[entityId] = nil
            end
        end
        -- Remove from quick lookup
        ClusterSystem.clusterMembers[entityId] = nil
    end
end

function ClusterSystem.getClusterForEntity(entityId)
    -- Check GameStateService first for latest data
    local gameState = GameStateService:getLatestState()
    if gameState then
        for _, cluster in ipairs(gameState.clusters) do
            if table.find(cluster.members, entityId) then
                return cluster
            end
        end
    end
    
    -- Fallback to InteractionService
    return InteractionService:getClusterForEntity(entityId)
end

return ClusterSystem 