local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")

local NPCChatMessageEvent = ReplicatedStorage:WaitForChild("NPCChatMessageEvent")

-- Print debug info
print("NPCChatClient: Starting initialization")
print("TextChatService available:", TextChatService ~= nil)

NPCChatMessageEvent.OnClientEvent:Connect(function(data)
    if not data or not data.npcName or not data.message then 
        warn("NPCChatClient: Received invalid chat data")
        return 
    end
    
    -- Format the message
    local formattedMessage = string.format("[%s] %s", data.npcName, data.message)
    print("NPCChatClient: Attempting to send message:", formattedMessage)
    
    -- Try to send directly to TextChatService
    local success, err = pcall(function()
        TextChatService:SendAsync(formattedMessage)
    end)
    
    if not success then
        warn("NPCChatClient: Failed to send message:", err)
        -- Try fallback to default channel
        pcall(function()
            if TextChatService.DefaultChannel then
                TextChatService.DefaultChannel:SendAsync(formattedMessage)
            end
        end)
    end
end)

print("NPCChatClient: Initialization complete") 