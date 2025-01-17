-- NPCClientHandler.client.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextService = game:GetService("TextService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Get the chat specific RemoteEvent
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
local currentNPCConversation = nil  -- Track which NPC we're talking to

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

-- Function to handle player chat messages
local function onPlayerChatted(message)
    -- Check if we're in a conversation with an NPC
    if currentNPCConversation then
        -- Send the message to the server
        NPCChatEvent:FireServer({
            npcName = currentNPCConversation,
            message = message
        })
    end
end

-- Handle incoming NPC chat messages
NPCChatEvent.OnClientEvent:Connect(function(data)
    if not data then return end

    -- Handle different types of messages
    if data.type == "started_conversation" then
        currentNPCConversation = data.npcName
        sendToChat("System", "Started conversation with " .. data.npcName)
    elseif data.type == "ended_conversation" then
        currentNPCConversation = nil
        sendToChat("System", "Ended conversation with " .. data.npcName)
    elseif data.npcName and data.message then
        sendToChat(data.npcName, data.message)
    end
end)

-- Connect to TextChatService for modern chat
local TextChatService = game:GetService("TextChatService")
if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
    TextChatService.SendingMessage:Connect(function(textChatMessage)
        onPlayerChatted(textChatMessage.Text)
    end)
end

-- Connect to legacy chat system
local player = Players.LocalPlayer
if player then
    player.Chatted:Connect(onPlayerChatted)
end

LoggerService:info("SYSTEM", "NPC Client Chat Handler initialized")