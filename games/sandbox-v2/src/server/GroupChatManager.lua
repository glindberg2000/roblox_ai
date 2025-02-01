-- GroupChatManager.lua: Handles group chat rounds with round-robin scheduling.
local LettaAPI = require(script.Parent.LettaAPI)  -- API handler for batch message processing
local ClusterManager = require(script.Parent.ClusterManager)  -- Provides NPC IDs in a cluster
local LoggerService = require(script.Parent.LoggerService)
local Router = require(script.Parent.ClusterMessageRouter)

local GroupChatManager = {}
GroupChatManager.__index = GroupChatManager

-- Process one round for a specific cluster
function GroupChatManager:process_cluster(cluster_id)
    local clusterQueue = Router.GlobalClusterQueue[cluster_id]
    if not clusterQueue then
        LoggerService:warn("GROUP_CHAT", "Missing queue for cluster: "..tostring(cluster_id))
        return
    end

    LoggerService:debug("GROUP_CHAT", string.format(
        "Processing cluster %s - Messages: %d, NPCs: %d",
        cluster_id,
        #clusterQueue.messages,
        #clusterQueue.npc_ids
    ))

    -- Update npc_ids in the cluster from ClusterManager
    clusterQueue.npc_ids = ClusterManager.get_npc_ids_in_cluster(cluster_id)

    if #clusterQueue.npc_ids == 0 then
        LoggerService:warn("GROUP_CHAT", "No NPCs currently in cluster " .. cluster_id)
        return
    end

    -- Determine current NPC turn (round-robin)
    local npc_index = clusterQueue.npc_turn_index
    local current_npc = clusterQueue.npc_ids[npc_index]

    if #clusterQueue.messages == 0 then
        -- No messages to process this round
        return
    end

    -- Form the current batch (copy messages)
    local batch = {}
    for _, msg in ipairs(clusterQueue.messages) do
        table.insert(batch, msg)
    end

    -- Clear the queue for the next batch round
    clusterQueue.messages = {}

    LoggerService:info("GROUP_CHAT", string.format("Processing batch for NPC %s in cluster %s", current_npc, cluster_id))
    
    -- Send the batch and process the response via Letta API
    LettaAPI:process_batch_for_npc(current_npc, batch)
        :andThen(function(response)
            -- Broadcast the response to all NPCs in the cluster
            GroupChatManager:broadcast_response(cluster_id, response)
            -- Advance round-robin pointer for next round
            clusterQueue.npc_turn_index = (npc_index % #clusterQueue.npc_ids) + 1
        end)
        :catch(function(err)
            LoggerService:error("GROUP_CHAT", "Error processing batch: " .. tostring(err))
            -- Optionally place batch back into queue or perform other error handling.
        end)
end

function GroupChatManager:broadcast_response(cluster_id, response)
    local npc_ids = Router.GlobalClusterQueue[cluster_id].npc_ids
    for _, npc_id in ipairs(npc_ids) do
        -- Each NPC is expected to have a method to process/broadcast a received response.
        local npc = ClusterManager.get_npc_by_id(npc_id)
        if npc then
            npc:receive_chat_response(response)
        end
    end
end

-- Scheduler: Checks all cluster queues periodically.
function GroupChatManager:start_scheduler()
    while true do
        LoggerService:debug("GROUP_CHAT", "Scheduler loop iteration")
        for cluster_id, _ in pairs(Router.GlobalClusterQueue) do
            self:process_cluster(cluster_id)
        end
        task.wait(1) -- One-second interval; adjust as needed.
    end
end

return setmetatable({}, GroupChatManager) 