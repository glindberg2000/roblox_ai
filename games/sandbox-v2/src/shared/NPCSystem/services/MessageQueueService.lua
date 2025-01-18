local MessageQueueService = {}
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(script.Parent.LoggerService)

-- Simple state tracking
local lastMessageTimes = {}
local COOLDOWN = 5

-- Initialize or get RemoteEvent
local function getOrCreateChatEvent()
    local event = ReplicatedStorage:FindFirstChild("NPCChatEvent")
    if not event then
        event = Instance.new("RemoteEvent")
        event.Name = "NPCChatEvent"
        event.Parent = ReplicatedStorage
        LoggerService:debug("CHAT", "Created NPCChatEvent")
    end
    return event
end

function MessageQueueService:enqueueMessage(npcName, text)
    local now = tick()
    if not lastMessageTimes[npcName] or now - lastMessageTimes[npcName] >= COOLDOWN then
        local NPCChatEvent = getOrCreateChatEvent()
        
        -- Send message
        NPCChatEvent:FireAllClients({
            npcName = npcName,
            message = text,
            type = "npc_chat"
        })
        
        lastMessageTimes[npcName] = now
        LoggerService:debug("CHAT", string.format("Message sent for %s: %s", npcName, text))
        return true
    end
    LoggerService:debug("CHAT", string.format("Message blocked by cooldown for %s", npcName))
    return false
end

function MessageQueueService:testMessage(npcName)
    LoggerService:debug("TEST", "Attempting to send test message to " .. npcName)
    return self:enqueueMessage(npcName, "Vive Libre")
end

return MessageQueueService 