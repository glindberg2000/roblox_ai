-- InteractionService.lua
local InteractionService = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local LoggerService = require(NPCSystem.services.LoggerService)

function InteractionService:checkRangeAndEndConversation(npc1, npc2)
    if not npc1.model or not npc2.model then return end
    if not npc1.model.PrimaryPart or not npc2.model.PrimaryPart then return end

    local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
    if distance > npc1.responseRadius then
        LoggerService:log("INTERACTION", string.format("%s and %s are out of range, ending conversation",
            npc1.displayName, npc2.displayName))
        return true
    end
    return false
end

function InteractionService:canInteract(npc1, npc2)
    -- Check if either NPC is already in conversation
    if npc1.inConversation or npc2.inConversation then
        return false
    end
    
    -- Check abilities
    if not npc1.abilities or not npc2.abilities then
        return false
    end
    
    -- Check if they can chat
    if not (table.find(npc1.abilities, "chat") and table.find(npc2.abilities, "chat")) then
        return false
    end
    
    return true
end

function InteractionService:lockNPCsForInteraction(npc1, npc2)
    npc1.inConversation = true
    npc2.inConversation = true
    npc1.movementState = "locked"
    npc2.movementState = "locked"
end

function InteractionService:unlockNPCsAfterInteraction(npc1, npc2)
    npc1.inConversation = false
    npc2.inConversation = false
    npc1.movementState = "free"
    npc2.movementState = "free"
end

return InteractionService 