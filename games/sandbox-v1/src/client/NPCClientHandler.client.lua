local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextService = game:GetService("TextService")

-- Get the chat specific RemoteEvent
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

-- Function to safely send a message to the chat system
local function sendToChat(npcName, message)
    -- Try to filter the message (optional but recommended)
    local success, filteredMessage = pcall(function()
        return TextService:FilterStringAsync(message, Players.LocalPlayer.UserId)
    end)
    
    if not success then
        filteredMessage = message -- Use original if filtering fails
    end
    
    -- Format the message with NPC name
    local formattedMessage = string.format("[%s] %s", npcName, filteredMessage)
    
    -- Send using legacy chat system
    if game:GetService("StarterGui"):GetCoreGuiEnabled(Enum.CoreGuiType.Chat) then
        game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
            Text = formattedMessage,
            Color = Color3.fromRGB(249, 217, 55),
            Font = Enum.Font.SourceSansBold
        })
    end
    
    -- Also try TextChatService if available
    local TextChatService = game:GetService("TextChatService")
    if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
        local channel = TextChatService.TextChannels:FindFirstChild("RBXGeneral")
        if channel then
            channel:DisplaySystemMessage(formattedMessage)
        end
    end
end

-- Handle incoming NPC chat messages
NPCChatEvent.OnClientEvent:Connect(function(data)
    if data and data.npcName and data.message then
        sendToChat(data.npcName, data.message)
    end
end)

print("NPC Client Chat Handler initialized")