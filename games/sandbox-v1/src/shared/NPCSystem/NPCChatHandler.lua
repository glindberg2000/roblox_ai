local function HandleChat(npcId, message, participant, context)
    Logger:log("DEBUG", string.format("NPCChatHandler: Received request %s", 
        HttpService:JSONEncode({
            message = message,
            npc_id = npcId,
            context = context
        })
    ))

    -- Try V4 first
    Logger:log("DEBUG", "NPCChatHandler: Attempting V4")
    local success, response = pcall(function()
        return V4ChatClient:SendMessage(npcId, message, participant, context)
    end)

    if success and response then
        Logger:log("DEBUG", string.format("NPCChatHandler: V4 succeeded %s", 
            HttpService:JSONEncode(response)
        ))
        return response
    end

    -- If V4 fails, try V3
    Logger:log("DEBUG", "NPCChatHandler: V4 failed, attempting V3")
    success, response = pcall(function()
        return V3ChatClient:SendMessage(npcId, message, participant, context)
    end)

    if success and response then
        Logger:log("DEBUG", "NPCChatHandler: V3 succeeded")
        return response
    end

    -- If both fail, return error
    Logger:log("ERROR", "NPCChatHandler: All chat attempts failed")
    return {
        message = "Sorry, I'm having trouble understanding right now.",
        action = { type = "none" }
    }
end 