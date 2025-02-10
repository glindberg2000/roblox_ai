local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)
local NPCChatHandler = require(ReplicatedStorage.Shared.NPCSystem.chat.NPCChatHandler)

local NPCChatEvent = ReplicatedStorage:FindFirstChild("NPCChatEvent") or Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

local NPCChatDisplay = {}

function NPCChatDisplay:displayMessage(npc, message, recipient)
    LoggerService:debug("CHAT", string.format(
        "Display message called - NPC: %s, Message: %s",
        npc.displayName,
        typeof(message) == "table" and message.text or message
    ))

    -- Check if this is an API response
    if typeof(message) == "table" and message.isApiResponse then
        -- Skip NPCChatHandler for API responses, only send to client
        if typeof(recipient) == "Instance" and recipient:IsA("Player") then
            NPCChatEvent:FireClient(recipient, {
                npcName = npc.displayName,
                message = message.text,
                type = "chat"
            })
        end
        return
    end

    -- Ensure we have a valid model and head
    if not npc.model then
        LoggerService:error("ERROR", string.format("Cannot display message - no model for %s", npc.displayName))
        return
    end
    
    if not npc.model:FindFirstChild("Head") then
        LoggerService:error("ERROR", string.format("Cannot display message - no head for %s", npc.displayName))
        return
    end

    -- Use NPCChatHandler to handle the message display
    local success, err = pcall(function()
        -- Create request in same format as handleNPCInteraction
        local request = {
            npc_id = npc.id,
            participant_id = recipient.UserId,
            message = message,
            context = {
                participant_name = recipient.Name,
                participant_type = "player",
                speaker_name = npc.displayName
            }
        }
        
        NPCChatHandler:HandleChat(request)
        LoggerService:debug("CHAT", "Sent message through NPCChatHandler")
    end)
    
    if not success then
        LoggerService:error("ERROR", string.format("Failed to send chat message: %s", err))
    end

    -- Fire event to specific client if recipient is a player
    if typeof(recipient) == "Instance" and recipient:IsA("Player") then
        LoggerService:debug("CHAT", "Firing NPCChatEvent to client")
        NPCChatEvent:FireClient(recipient, {
            npcName = npc.displayName,
            message = message,
            type = "chat"
        })
    end
end

return NPCChatDisplay 