local ConversationManager = {}

-- Track active conversations and message types
local activeConversations = {
    playerToNPC = {}, -- player UserId -> {npc = npcRef, lastMessage = time}
    npcToNPC = {},    -- npc Id -> {partner = npcRef, lastMessage = time}
    npcToPlayer = {}  -- npc Id -> {player = playerRef, lastMessage = time}
}

-- Message types
local MessageType = {
    SYSTEM = "system",
    CHAT = "chat"
}

function ConversationManager:isSystemMessage(message)
    return string.match(message, "^%[SYSTEM%]")
end

function ConversationManager:canStartConversation(sender, receiver)
    -- Check if either participant is in conversation
    if self:isInConversation(sender) or self:isInConversation(receiver) then
        return false
    end
    return true
end

function ConversationManager:isInConversation(participant)
    local id = self:getParticipantId(participant)
    local participantType = self:getParticipantType(participant)
    
    if participantType == "player" then
        return activeConversations.playerToNPC[id] ~= nil
    else
        return activeConversations.npcToPlayer[id] ~= nil or 
               activeConversations.npcToNPC[id] ~= nil
    end
end

function ConversationManager:lockConversation(sender, receiver)
    local senderId = self:getParticipantId(sender)
    local receiverId = self:getParticipantId(receiver)
    local senderType = self:getParticipantType(sender)
    local receiverType = self:getParticipantType(receiver)
    
    if senderType == "player" and receiverType == "npc" then
        activeConversations.playerToNPC[senderId] = {
            npc = receiver,
            lastMessage = os.time()
        }
        activeConversations.npcToPlayer[receiverId] = {
            player = sender,
            lastMessage = os.time()
        }
    elseif senderType == "npc" and receiverType == "npc" then
        activeConversations.npcToNPC[senderId] = {
            partner = receiver,
            lastMessage = os.time()
        }
        activeConversations.npcToNPC[receiverId] = {
            partner = sender,
            lastMessage = os.time()
        }
    end
end

function ConversationManager:routeMessage(message, sender, intendedReceiver)
    -- Allow system messages to pass through
    if self:isSystemMessage(message) then
        return intendedReceiver
    end
    
    -- Get current conversation partner if any
    local currentPartner = self:getCurrentPartner(sender)
    if currentPartner then
        return currentPartner
    end
    
    -- If no active conversation, try to start one
    if self:canStartConversation(sender, intendedReceiver) then
        self:lockConversation(sender, intendedReceiver)
        return intendedReceiver
    end
    
    return nil
end

-- Helper functions
function ConversationManager:getParticipantId(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return participant.UserId
    else
        return participant.npcId
    end
end

function ConversationManager:getParticipantType(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return "player"
    else
        return "npc"
    end
end

return ConversationManager 