local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Add at the top with other variables
local recentMessages = {}
local MESSAGE_CACHE_TIME = 0.1

-- Add helper function
local function generateMessageId(npcId, message)
    return string.format("%s_%s", npcId, message)
end

-- Modify the chat event handler
local function onNPCChat(npcName, message)
    -- Generate message ID
    local messageId = generateMessageId(npcName, message)
    
    -- Check for duplicate message
    if recentMessages[messageId] then
        if tick() - recentMessages[messageId] < MESSAGE_CACHE_TIME then
            LoggerService:debug("CHAT", "Skipping duplicate message: " .. messageId)
            return -- Skip duplicate message
        end
    end
    
    -- Store message timestamp
    recentMessages[messageId] = tick()
    
    -- Clean up old messages
    for id, timestamp in pairs(recentMessages) do
        if tick() - timestamp > MESSAGE_CACHE_TIME then
            recentMessages[id] = nil
        end
    end
    
    LoggerService:debug("CHAT", string.format("Adding chat message from %s: %s", npcName, message))
    
    -- Add message to chat
    game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
        Text = string.format("[%s]: %s", npcName, message),
        Color = Color3.fromRGB(255, 170, 0)
    })
end

-- Connect event handler
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
NPCChatEvent.OnClientEvent:Connect(onNPCChat)

LoggerService:info("SYSTEM", "NPC Client Chat Handler initialized") 