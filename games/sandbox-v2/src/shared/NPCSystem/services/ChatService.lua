function ChatService:displayMessage(npc, messageData)
    -- Show who's talking in group chat
    local prefix = string.format("[%s] ", messageData.sender)
    
    -- Display in chat bubble and chat log
    self:showChatBubble(npc, prefix .. messageData.content)
    self:addToChatLog(messageData.sender, messageData.content, messageData.context)
end 