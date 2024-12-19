local ActionService = {}

local LoggerService = {
    debug = function(_, category, message)
        print(string.format("[DEBUG] [%s] %s", category, message))
    end,
    warn = function(_, category, message)
        warn(string.format("[WARN] [%s] %s", category, message))
    end
}

local MovementService = require(ReplicatedStorage.Shared.NPCSystem.services.MovementService)

-- Follow Action
function ActionService.follow(npc, target, options)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is following target %s", npc.displayName, target.Name))
    if npc and target then
        -- Delegate to MovementService for follow behavior
        MovementService:startFollowing(npc, target, options)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Target provided for follow action")
    end
end

-- Unfollow Action
function ActionService.unfollow(npc)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s stopped following", npc.displayName))
    if npc then
        -- Delegate to MovementService to stop following
        MovementService:stopFollowing(npc)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC provided for unfollow action")
    end
end

-- Chat Action
function ActionService.chat(npc, message)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is chatting: %s", npc.displayName, message))
    if npc and message then
        -- Example chat bubble logic
        local chatEvent = game.ReplicatedStorage:FindFirstChild("NPCChatEvent")
        if chatEvent then
            chatEvent:FireAllClients(npc, message)
        else
            LoggerService:warn("ACTION_SERVICE", "NPCChatEvent not found in ReplicatedStorage")
        end
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Message provided for chat action")
    end
end

-- Placeholder for additional actions
function ActionService.moveTo(npc, position)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is moving to position: %s", npc.displayName, tostring(position)))
    if npc and position then
        MovementService:moveNPCToPosition(npc, position)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Position provided for moveTo action")
    end
end

return ActionService