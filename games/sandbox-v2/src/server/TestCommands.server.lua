local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local NPCManagerV3 = require(ReplicatedStorage.Shared.NPCSystem.NPCManagerV3)
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Create a command system
local function handleChatCommand(player, message)
    -- Check if message starts with "!"
    if not message:sub(1,1) == "!" then return end
    
    local command = message:sub(2):lower() -- Remove "!" and convert to lowercase
    local npcManager = NPCManagerV3.getInstance()
    
    if command == "testjump" then
        LoggerService:debug("TEST", "Running jump test command")
        local npc = npcManager:getNPCByName("Pete")
        if npc then
            npcManager:executeAction(npc, player, {type = "jump"})
        else
            LoggerService:warn("TEST", "Could not find NPC Pete for test")
        end
    end
end

-- Connect to chat events
Players.PlayerAdded:Connect(function(player)
    player.Chatted:Connect(function(message)
        handleChatCommand(player, message)
    end)
end)

LoggerService:info("SYSTEM", "Test commands initialized") 