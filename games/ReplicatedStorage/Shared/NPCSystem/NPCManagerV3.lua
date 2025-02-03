function NPCManagerV3:createChatContext(npc, participant)
    local clusterMembers = self:getClusterMembers(npc)
    
    -- Separate into players and NPCs
    local nearbyPlayers = {}
    local nearbyNPCs = {}
    
    for _, entity in ipairs(clusterMembers) do
        if entity.type == "player" then
            table.insert(nearbyPlayers, entity.name)
        elseif entity.type == "npc" then
            table.insert(nearbyNPCs, entity.name)
        end
    end
    
    LoggerService:debug("CHAT", string.format(
        "Found nearby entities for %s: %d players, %d NPCs",
        npc.displayName,
        #nearbyPlayers,
        #nearbyNPCs
    ))
    
    local context = {
        participant_name = participant.Name,
        participant_type = participant:GetParticipantType(),
        participant_id = participant:GetParticipantId(),
        npc_location = npc.currentLocation or "Unknown",
        nearby_players = nearbyPlayers,
        nearby_npcs = nearbyNPCs
    }
    
    return context
end

function NPCManagerV3:createNPC(npcData)
    local npc = {
        id = HttpService:GenerateGUID(),
        displayName = npcData.displayName,
        abilities = npcData.abilities or {},
        model = nil,
        isInteracting = false,
        getInteractionHistory = function()
            return {}
        end
        -- ... rest of NPC properties
    }
    
    -- ... rest of createNPC function
end 