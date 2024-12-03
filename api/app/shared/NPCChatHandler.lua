function NPCChatHandler:HandleChat(request)
    print("NPCChatHandler: Received request", HttpService:JSONEncode(request))
    
    -- Add participant type if not set
    if not request.context then request.context = {} end
    if not request.context.participant_type then
        request.context.participant_type = request.npc_id and "npc" or "player"
    end
    
    -- Try V4 first
    print("NPCChatHandler: Attempting V4")
    local response = V4ChatClient:SendMessage(request)
    
    -- Fall back to V3 if needed
    if not response.success and response.shouldFallback then
        print("NPCChatHandler: Falling back to V3", response.error)
        return V3ChatClient:SendMessage(request)
    end
    
    print("NPCChatHandler: V4 succeeded", HttpService:JSONEncode(response))
    return response
end 