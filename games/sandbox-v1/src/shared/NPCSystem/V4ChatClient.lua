local V4ChatClient = {}

-- Update SendMessage signature to include participant
function V4ChatClient:SendMessage(npcId, message, participant, context)
    Logger:log("DEBUG", "V4ChatClient:SendMessage called")
    
    -- Try Letta chat first
    local response = self:handleLettaChat(npcId, message, participant, context)
    if response then
        return response
    end
    
    -- If Letta fails, try fallback
    return self:handleFallbackChat(npcId, message, participant, context)
end

-- Update handleLettaChat to handle NPC participants
function V4ChatClient:handleLettaChat(npcId, message, participant, context)
    Logger:log("DEBUG", "Attempting Letta chat first...")
    
    -- Log raw incoming data
    Logger:log("DEBUG", string.format("Raw incoming data: %s", HttpService:JSONEncode({
        message = message,
        npc_id = npcId,
        context = context
    })))
    
    -- Determine participant type and ID
    local participantType = "player"
    local participantId = participant.UserId
    local participantName = participant.Name
    
    if typeof(participant) ~= "Instance" or not participant:IsA("Player") then
        participantType = "npc"
        participantId = participant.id
        participantName = participant.displayName
    end
    Logger:log("DEBUG", string.format("Determined participant type: %s", participantType))
    
    -- Build request data
    local requestData = {
        message = message,
        npc_id = npcId,
        participant_type = participantType,
        participant_id = participantId,
        context = {
            participant_name = participantName,
            interaction_history = context.interaction_history or {},
            participant_type = participantType,
            is_new_conversation = context.is_new_conversation or false,
            npc_location = context.npc_location or "Unknown",
            nearby_players = context.nearby_players or {}
        }
    }
end 