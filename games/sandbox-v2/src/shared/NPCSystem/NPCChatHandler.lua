function NPCChatHandler:HandleChat(request)
    LoggerService:debug("CHAT", "NPCChatHandler: Starting chat handling")
    LoggerService:debug("CHAT", string.format(
        "Request context: %s",
        HttpService:JSONEncode(request.context)
    ))
    
    -- Rest of the code...
end 