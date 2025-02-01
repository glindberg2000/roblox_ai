-- GroupChatIntegration.lua
-- This module integrates group chat routing and round-robin processing.
-- It simulates receiving chat messages, routes them using the ClusterMessageRouter,
-- and starts the scheduler to process batches.

local ClusterMessageRouter = require(script.Parent.ClusterMessageRouter)
local GroupChatManager = require(script.Parent.GroupChatManager)
local LoggerService = require(script.Parent.LoggerService)
local ClusterManager = require(script.Parent.ClusterManager)  -- Make sure this exposes get_npc_ids_in_cluster and get_npc_by_id

LoggerService:info("GROUP_CHAT", "GroupChatIntegration module loaded.")

-- Sample function to simulate an incoming chat message.
local function simulateChatMessage(content, sender, cluster_id)
    local message = {
        content = content,
        sender = sender,
        cluster_id = cluster_id
    }
    LoggerService:debug("GROUP_CHAT", "Simulating chat message: " .. content .. " from " .. sender)
    ClusterMessageRouter.route_message(message)
end

-- Integration Setup:
-- Start the group chat scheduler in a separate task.
task.spawn(function()
    LoggerService:info("GROUP_CHAT", "Starting GroupChatManager scheduler...")
    GroupChatManager:start_scheduler()
    
    -- Verify scheduler started
    delay(3, function()
        LoggerService:debug("GROUP_CHAT", "Scheduler status check")
    end)
end)

-- For testing purposes, simulate messages.
-- In a real scenario, you would call ClusterMessageRouter.route_message() when a chat message is received.
-- Also, ensure that ClusterManager returns valid NPC IDs for a given cluster.
local TEST_CLUSTER_ID = "test_cluster_1"  -- Use a test cluster ID

-- (For testing, we will simulate some NPCs being present in the cluster manually)
do
    -- Ensure ClusterManager has at least some test NPCs.
    if ClusterManager.set_test_npc_ids then
        ClusterManager.set_test_npc_ids(TEST_CLUSTER_ID, { "npc1", "npc2", "npc3" })
    else
        LoggerService:warn("GROUP_CHAT", "ClusterManager does not support test NPC injection. Ensure real NPCs are in the cluster.")
    end
end

-- Simulate incoming chat messages at intervals.
task.spawn(function()
    while true do
        simulateChatMessage("Hello from PlayerA", "PlayerA", TEST_CLUSTER_ID)
        task.wait(0.5)
        simulateChatMessage("Hi from PlayerB", "PlayerB", TEST_CLUSTER_ID)
        task.wait(0.7)
        simulateChatMessage("Message from PlayerC", "PlayerC", TEST_CLUSTER_ID)
        task.wait(1)
    end
end)

-- This module does not return a value; it's intended to be loaded on the server to activate group chat integration. 