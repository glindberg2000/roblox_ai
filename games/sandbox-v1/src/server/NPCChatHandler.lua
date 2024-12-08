function NPCChatHandler:handleResponse(response, npc, participant)
    -- Check if this is a player interaction
    local participantType = typeof(participant) == "Instance" and participant:IsA("Player") and "player" or "npc"
    
    -- Store conversation history
    npc.chatHistory = npc.chatHistory or {}
    table.insert(npc.chatHistory, {
        message = response.message,
        timestamp = os.time(),
        sender = npc.displayName
    })

    -- Handle player interactions
    if participantType == "player" then
        -- Always prioritize player interactions
        npc.isInteracting = true
        npc.interactingPlayer = participant
        npc.isWindingDown = false
        npc.isEndingConversation = false
        
        -- Remove any end conversation flags
        if response.metadata then
            response.metadata.should_end = nil
        end
        
        -- Force end any NPC conversations
        if npc.currentParticipant and typeof(npc.currentParticipant) ~= "Instance" then
            NPCManagerV3:endInteraction(npc, npc.currentParticipant)
        end
    else
        -- For NPC conversations
        if npc.interactingPlayer then
            -- If talking to a player, don't process NPC chat
            return nil
        end
        
        -- Only allow natural endings for NPC-NPC conversations
        if response.metadata and response.metadata.should_end then
            npc.isWindingDown = true
        end
    end

    -- Include chat history in context
    if not response.context then
        response.context = {}
    end
    response.context.interaction_history = npc.chatHistory

    return response
end 