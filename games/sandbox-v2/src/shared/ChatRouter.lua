local ChatRouter = {}

function ChatRouter.new()
    local self = setmetatable({}, {__index = ChatRouter})
    self.activeConversations = {
        playerToNPC = {}, -- player UserId -> NPC reference
        npcToPlayer = {}, -- NPC id -> player reference
        npcToNPC = {}     -- NPC id -> NPC reference
    }
    return self
end

function ChatRouter:isInConversation(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return self.activeConversations.playerToNPC[participant.UserId] ~= nil
    else
        return self.activeConversations.npcToPlayer[participant.npcId] ~= nil or 
               self.activeConversations.npcToNPC[participant.npcId] ~= nil
    end
end

function ChatRouter:getCurrentPartner(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return self.activeConversations.playerToNPC[participant.UserId]
    else
        return self.activeConversations.npcToPlayer[participant.npcId] or
               self.activeConversations.npcToNPC[participant.npcId]
    end
end

function ChatRouter:lockConversation(participant1, participant2)
    if typeof(participant1) == "Instance" and participant1:IsA("Player") then
        self.activeConversations.playerToNPC[participant1.UserId] = participant2
        self.activeConversations.npcToPlayer[participant2.npcId] = participant1
    else
        self.activeConversations.npcToNPC[participant1.npcId] = participant2
        self.activeConversations.npcToNPC[participant2.npcId] = participant1
    end
end

function ChatRouter:unlockConversation(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        local npc = self.activeConversations.playerToNPC[participant.UserId]
        if npc then
            self.activeConversations.playerToNPC[participant.UserId] = nil
            self.activeConversations.npcToPlayer[npc.npcId] = nil
        end
    else
        local partner = self.activeConversations.npcToNPC[participant.npcId]
        if partner then
            self.activeConversations.npcToNPC[participant.npcId] = nil
            self.activeConversations.npcToNPC[partner.npcId] = nil
        end
    end
end

function ChatRouter:routeMessage(message, sender, intendedReceiver)
    -- Get current conversation partner if any
    local currentPartner = self:getCurrentPartner(sender)
    
    -- If in conversation, force route to current partner
    if currentPartner then
        return currentPartner
    end
    
    -- If not in conversation and both participants are free, lock them
    if not self:isInConversation(sender) and not self:isInConversation(intendedReceiver) then
        self:lockConversation(sender, intendedReceiver)
        return intendedReceiver
    end
    
    return nil -- Cannot route message
end

return ChatRouter 