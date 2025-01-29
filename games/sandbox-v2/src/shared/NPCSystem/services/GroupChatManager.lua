local GroupChatManager = {
    BATCH_SIZE = 5,  -- Process 5 messages at a time
    PROCESS_INTERVAL = 1  -- Process every second
}

function GroupChatManager.new()
    local self = setmetatable({}, {__index = GroupChatManager})
    self.activeGroups = {}
    self.messageQueue = {}
    
    -- Start message processing loop
    task.spawn(function()
        while true do
            task.wait(self.PROCESS_INTERVAL)
            if self.activeGroups then
                for groupId, _ in pairs(self.activeGroups) do
                    self:processGroup(groupId)
                end
            end
        end
    end)
    
    return self
end

function GroupChatManager:addGroup(groupId, members)
    self.activeGroups[groupId] = {
        id = groupId,
        members = members
    }
end

function GroupChatManager:queueMessage(groupId, messageData)
    if not self.messageQueue[groupId] then
        self.messageQueue[groupId] = {}
    end
    
    -- Validate message data
    if not messageData.message or not messageData.sender then
        LoggerService:warn("CHAT", "Invalid message data for group chat")
        return
    end
    
    table.insert(self.messageQueue[groupId], messageData)
    
    LoggerService:info("CHAT", string.format(
        "Queued message for group %s: %s",
        groupId,
        messageData.message
    ))
end

function GroupChatManager:processGroup(groupId)
    local group = self.activeGroups[groupId]
    if not group then return end
    
    local messages = self.messageQueue[groupId]
    if not messages or #messages == 0 then return end
    
    -- Process messages
    local processed = 0
    while processed < self.BATCH_SIZE and #messages > 0 do
        local msg = table.remove(messages, 1)
        
        -- Create shared context
        local sharedContext = {
            participant_type = msg.sender.Type or "npc",
            participant_name = msg.sender.displayName or msg.sender.Name,
            speaker_name = msg.sender.displayName or msg.sender.Name,
            group_id = groupId,
            group_size = #group.members,
            group_members = {},
            message_type = "group_chat",
            nearby_players = {}
        }
        
        -- Add member names to context
        for _, member in ipairs(group.members) do
            if member.displayName then
                table.insert(sharedContext.group_members, member.displayName)
            end
        end
        
        -- Broadcast to all members except sender
        for _, member in ipairs(group.members) do
            if member.id ~= msg.sender.id then
                LoggerService:info("CHAT", string.format(
                    "Broadcasting group message from %s to %s: %s",
                    msg.sender.displayName or msg.sender.Name,
                    member.displayName,
                    msg.message
                ))
                
                -- Use NPCChatHandler with proper parameters
                local response = NPCChatHandler:HandleChat({
                    message = msg.message,
                    npc = member,
                    participant = msg.sender,
                    context = sharedContext
                })
                
                if response then
                    member:handleMessage(msg.message, msg.sender, sharedContext)
                end
            end
        end
        
        processed = processed + 1
    end
end

return GroupChatManager 