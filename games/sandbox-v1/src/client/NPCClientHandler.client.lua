-- StarterPlayerScripts/NPCClientHandler.client.lua

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

-- Initialize Logger
local Logger
local function initializeLogger()
    local success, result = pcall(function()
        return require(ReplicatedStorage:WaitForChild("Logger", 10))
    end)

    if success then
        Logger = result
    else
        -- Fallback logger
        Logger = {
            log = function(_, category, message)
                print(string.format("[%s] %s", category, message))
            end
        }
    end
end

initializeLogger()

local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

NPCChatEvent.OnClientEvent:Connect(function(npcName, message)
    if message ~= "The interaction has ended." then
        Logger:log("CHAT", string.format("Received NPC message: %s - %s", npcName, message))

        -- Display in chat box
        local textChannel = TextChatService.TextChannels.RBXGeneral
        if textChannel then
            textChannel:DisplaySystemMessage(npcName .. ": " .. message)
            Logger:log("CHAT", string.format("Message displayed in chat: %s: %s", npcName, message))
        else
            Logger:log("ERROR", "RBXGeneral text channel not found")
        end

        Logger:log("CHAT", string.format("NPC Chat processed - %s: %s", npcName, message))
    else
        Logger:log("CHAT", string.format("Interaction ended with %s", npcName))
    end
end)

Logger:log("SYSTEM", "NPC Client Chat Handler loaded")
