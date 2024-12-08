local ChatService = game:GetService("Chat")

-- Initialize chat service
local function initializeChat()
    local success, err = pcall(function()
        -- Enable chat bubbles
        ChatService:SetBubbleChatSettings({
            BubbleDuration = 10,
            MaxDistance = 80,
            BackgroundColor3 = Color3.fromRGB(255, 255, 255),
            TextColor3 = Color3.fromRGB(0, 0, 0),
            TextSize = 16
        })
    end)
    
    if not success then
        warn("Failed to initialize chat:", err)
    end
end

return {
    initialize = initializeChat
} 