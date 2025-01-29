-- New module to handle group conversations
local GroupChatManager = {
    activeGroups = {},
    messageQueue = {},
    BATCH_SIZE = 5,  -- Process 5 messages at a time
    PROCESS_INTERVAL = 1  -- Process every second
}

function GroupChatManager.new()
    local self = setmetatable({}, {__index = GroupChatManager})
    
    -- Structure for group chat:
    -- {
    --     groupId = {
    --         members = {npc1, npc2, ...},
    --         messages = {}, -- Recent messages only
    --         currentSpeaker = 1, -- Index of current NPC to respond
    --         lastUpdate = 0
    --     }
    -- }
    
    return self
end

function GroupChatManager:queueMessage(groupId, message, sender)
    if not self.messageQueue[groupId] then
        self.messageQueue[groupId] = {}
    end
    
    table.insert(self.messageQueue[groupId], {
        content = message,
        sender = sender,
        timestamp = os.time()
    })
end

function GroupChatManager:processGroup(groupId)
    local group = self.activeGroups[groupId]
    if not group or #self.messageQueue[groupId] == 0 then return end
    
    -- Get current speaker
    local speaker = group.members[group.currentSpeaker]
    if not speaker then return end
    
    -- Collect recent messages
    local recentMessages = {}
    for i = math.max(1, #self.messageQueue[groupId] - self.BATCH_SIZE), #self.messageQueue[groupId] do
        table.insert(recentMessages, self.messageQueue[groupId][i])
    end
    
    -- Format messages for API
    local messageBlock = {
        messages = recentMessages,
        group = group.members,
        speaker = speaker
    }
    
    -- Send to API
    local response = NPCChatHandler:HandleGroupChat(messageBlock)
    
    -- Move to next speaker
    group.currentSpeaker = (group.currentSpeaker % #group.members) + 1
    
    return response
end 