local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")

local NPCChatMessageEvent = ReplicatedStorage:WaitForChild("NPCChatMessageEvent")

-- Function to send NPC chat message
local function sendNPCChatMessage(npcName, messageText)
    local textChatMessage = TextChatService:CreateMessage()
    textChatMessage.Text = string.format("[%s] %s", npcName, messageText)
    textChatMessage.TextSource = nil -- Makes the message appear as a system message
    TextChatService:SendTextMessage(textChatMessage)
end

NPCChatMessageEvent.OnClientEvent:Connect(function(data)
    -- Send message to chat
    sendNPCChatMessage(data.npcName, data.message)
    
    -- Also create chat bubble
    local Chat = game:GetService("Chat")
    local character = game.Players.LocalPlayer.Character
    if character then
        Chat:Chat(character.Head, data.message)
    end
end) 