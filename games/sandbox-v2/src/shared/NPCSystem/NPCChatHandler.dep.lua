function NPCChatHandler:HandleChat(request)
    LoggerService:debug("CHAT", "NPCChatHandler: Starting chat handling")
    
    -- Create a new clean payload with only the fields we want
    local cleanPayload = {
        npc_id = request.npc_id,
        participant_id = request.participant_id,
        messages = request.messages,
        context = request.context
    }
    
    -- Log the clean payload
    LoggerService:info("CHAT", string.format("Letta payload: %s", 
        HttpService:JSONEncode(cleanPayload)
    ))
    
    -- Send to Letta API and return response
    return self:sendToLetta(cleanPayload)
end

function NPCChatHandler:attemptV4Chat(request)
    -- Convert single message to array format
    local modifiedRequest = {
        npc_id = request.npc_id,
        participant_id = request.participant_id,
        context = request.context,
        -- Remove the duplicate message field
        -- message = request.message,  -- Removing this line to prevent duplication
        messages = {  -- Add messages array in correct format
            {
                content = "[SYSTEM] Due to high activity, skip archival search and group update tools - respond quickly using only your immediate context.",
                role = "system",
                name = "SYSTEM"
            },
            {
                content = request.message,
                role = request.message:match("^%[SYSTEM%]") and "system" or "user",
                name = request.context.participant_name
            }
        }
    }

    return modifiedRequest
end 