-- ConversationManagerV2.lua
-- A robust conversation management system for NPC interactions
-- Version: 1.0.0
-- Place in: game.ServerScriptService.Shared

local ConversationManagerV2 = {}
ConversationManagerV2.__index = ConversationManagerV2

-- Constants
local CONVERSATION_TIMEOUT = 300 -- 5 minutes
local MAX_HISTORY_LENGTH = 50
local MAX_CONVERSATIONS_PER_NPC = 5

-- Conversation types enum
ConversationManagerV2.Types = {
    NPC_USER = "npc_user",
    NPC_NPC = "npc_npc",
    GROUP = "group"
}

-- Private storage
local conversations = {}
local activeParticipants = {}

-- Utility functions
local function generateConversationId()
    return game:GetService("HttpService"):GenerateGUID(false)
end

local function getCurrentTime()
    return os.time()
end

local function isValidParticipant(participant)
    return participant and (
        (typeof(participant) == "Instance" and participant:IsA("Player")) or
        (participant.GetParticipantType and participant:GetParticipantType() == "npc")
    )
end

-- Conversation object constructor
function ConversationManagerV2.new()
    local self = setmetatable({}, ConversationManagerV2)
    self:startCleanupTask()
    return self
end

-- Core conversation management functions
function ConversationManagerV2:createConversation(type, participant1, participant2)
    -- Validate participants
    if not isValidParticipant(participant1) or not isValidParticipant(participant2) then
        warn("Invalid participants provided to createConversation")
        return nil
    end

    -- Generate unique ID
    local conversationId = generateConversationId()
    
    -- Create conversation structure
    conversations[conversationId] = {
        id = conversationId,
        type = type,
        participants = {
            [participant1.UserId or participant1.id] = true,
            [participant2.UserId or participant2.id] = true
        },
        messages = {},
        created = getCurrentTime(),
        lastUpdate = getCurrentTime(),
        metadata = {}
    }

    -- Update participant tracking
    local p1Id = participant1.UserId or participant1.id
    local p2Id = participant2.UserId or participant2.id
    
    activeParticipants[p1Id] = activeParticipants[p1Id] or {}
    activeParticipants[p2Id] = activeParticipants[p2Id] or {}
    
    activeParticipants[p1Id][conversationId] = true
    activeParticipants[p2Id][conversationId] = true

    return conversationId
end

function ConversationManagerV2:addMessage(conversationId, sender, message)
    local conversation = conversations[conversationId]
    if not conversation then
        warn("Attempt to add message to nonexistent conversation:", conversationId)
        return false
    end

    -- Add message with metadata
    table.insert(conversation.messages, {
        sender = sender.UserId or sender.id,
        content = message,
        timestamp = getCurrentTime()
    })

    -- Trim history if needed
    if #conversation.messages > MAX_HISTORY_LENGTH then
        table.remove(conversation.messages, 1)
    end

    conversation.lastUpdate = getCurrentTime()
    return true
end

function ConversationManagerV2:getHistory(conversationId, limit)
    local conversation = conversations[conversationId]
    if not conversation then
        return {}
    end

    limit = limit or MAX_HISTORY_LENGTH
    local messages = {}
    local startIndex = math.max(1, #conversation.messages - limit + 1)
    
    for i = startIndex, #conversation.messages do
        table.insert(messages, conversation.messages[i].content)
    end

    return messages
end

function ConversationManagerV2:endConversation(conversationId)
    local conversation = conversations[conversationId]
    if not conversation then
        return false
    end

    -- Remove from participant tracking
    for participantId in pairs(conversation.participants) do
        if activeParticipants[participantId] then
            activeParticipants[participantId][conversationId] = nil
        end
    end

    -- Remove conversation
    conversations[conversationId] = nil
    return true
end

-- Cleanup task
function ConversationManagerV2:startCleanupTask()
    task.spawn(function()
        while true do
            local currentTime = getCurrentTime()
            
            -- Check for expired conversations
            for id, conversation in pairs(conversations) do
                if currentTime - conversation.lastUpdate > CONVERSATION_TIMEOUT then
                    self:endConversation(id)
                end
            end
            
            task.wait(60) -- Run cleanup every minute
        end
    end)
end

-- Utility methods
function ConversationManagerV2:getActiveConversations(participantId)
    return activeParticipants[participantId] or {}
end

function ConversationManagerV2:isParticipantInConversation(participantId, conversationId)
    local conversation = conversations[conversationId]
    return conversation and conversation.participants[participantId] or false
end

function ConversationManagerV2:getConversationMetadata(conversationId)
    local conversation = conversations[conversationId]
    return conversation and conversation.metadata or nil
end

function ConversationManagerV2:updateMetadata(conversationId, key, value)
    local conversation = conversations[conversationId]
    if conversation then
        conversation.metadata[key] = value
        return true
    end
    return false
end

return ConversationManagerV2