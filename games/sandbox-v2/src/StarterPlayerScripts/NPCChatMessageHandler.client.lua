local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")
local Players = game:GetService("Players")

local NPCSystem = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("NPCSystem")
local ChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent", 5) or Instance.new("RemoteEvent")
ChatEvent.Name = "NPCChatEvent"
ChatEvent.Parent = ReplicatedStorage

-- Handle incoming chat messages
TextChatService.OnIncomingMessage = function(message)
    local player = Players.LocalPlayer
    if not player then return end
    
    -- Only handle messages from this player
    if message.TextSource.UserId ~= player.UserId then return end
    
    -- Send to server for NPC processing
    ChatEvent:FireServer(message.Text)
end 