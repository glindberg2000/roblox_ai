local ReplicatedStorage = game:GetService("ReplicatedStorage")
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

local Logger = require(ReplicatedStorage:WaitForChild("Logger"))
Logger:log("SYSTEM", "NPC Client Chat Handler loaded")

-- Handle incoming NPC chat messages
NPCChatEvent.OnClientEvent:Connect(function(npcName, message, metadata)
    Logger:log("CHAT", string.format("Received NPC message: %s - %s", npcName, message))
    
    -- Display in chat
    game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
        Text = string.format("%s: %s", npcName, message),
        Color = metadata and metadata.type == "npc_to_npc" and Color3.fromRGB(200, 200, 255) or Color3.fromRGB(200, 255, 200)
    })
    
    Logger:log("CHAT", string.format("Message displayed in chat: %s: %s", npcName, message))
    Logger:log("CHAT", string.format("NPC Chat processed - %s: %s", npcName, message))
end) 