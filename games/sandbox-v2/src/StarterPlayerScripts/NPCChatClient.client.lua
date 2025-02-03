-- NPCChatClient.client.lua

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

local NPCChatMessageEvent = ReplicatedStorage:WaitForChild("NPCChatMessageEvent")

-- Log when we get the system channel
local systemChannel = nil
local success, err = pcall(function()
    LoggerService:debug("CHAT", "Waiting for RBXSystem channel...")
    systemChannel = TextChatService.TextChannels:WaitForChild("RBXSystem")
    LoggerService:debug("CHAT", "Got RBXSystem channel")
end)

if not success then
    LoggerService:error("CHAT", "Failed to get system channel: " .. tostring(err))
    return
end

NPCChatMessageEvent.OnClientEvent:Connect(function(data)
    LoggerService:debug("CHAT", string.format("Client received message from %s: %s", data.npcName, data.message))
    
    -- Display system message on client
    local success, err = pcall(function()
        LoggerService:debug("CHAT", "Attempting to display message...")
        systemChannel:DisplaySystemMessage(string.format("[%s] %s", data.npcName, data.message))
        LoggerService:debug("CHAT", "Message displayed successfully")
    end)
    
    if not success then
        LoggerService:error("CHAT", "Failed to display message: " .. tostring(err))
    end
end)

LoggerService:info("CHAT", "NPC chat client fully initialized") 