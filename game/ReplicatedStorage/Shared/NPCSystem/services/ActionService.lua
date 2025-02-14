local function handleAction(npc, actionData)
    if not actionData then return end
    
    local actionType = actionData.type
    local data = actionData.data
    
    if actionType == "emote" then
        -- New standard format uses type and target
        local emoteType = data.type
        local targetPlayer = data.target
        
        if not emoteType then
            warn("Missing emote type in action data")
            return
        end
        
        EmoteService:performEmote(npc, emoteType, targetPlayer)
        
    elseif actionType == "patrol" then
        -- New standard format uses target and type
        local area = data.target  -- Location to patrol
        local style = data.type   -- Patrol style
        
        PatrolService:startPatrol(npc, area, style)
        
    -- Handle other actions...
    end
end 