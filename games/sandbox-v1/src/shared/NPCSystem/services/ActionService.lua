local ReplicatedStorage = game:GetService("ReplicatedStorage")

local LoggerService = {
    debug = function(_, category, message)
        print(string.format("[DEBUG] [%s] %s", category, message))
    end,
    warn = function(_, category, message)
        warn(string.format("[WARN] [%s] %s", category, message))
    end
}

local NPCManagerV3 = require(ReplicatedStorage.Shared.NPCSystem.NPCManagerV3)
local movementServiceInstance = NPCManagerV3.getInstance().movementService

local ActionService = {}

function ActionService.follow(npc, target)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is following %s", npc.displayName, target.Name))

    if not target or not target.Character then
        LoggerService:warn("ACTION_SERVICE", "Invalid target or no character to follow")
        return
    end

    npc.isFollowing = true
    npc.followTarget = target
    npc.followStartTime = tick()
    npc.isWalking = false

    movementServiceInstance:startFollowing(npc, target.Character, {
        distance = 5,
        updateRate = 0.1
    })

    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s follow state set -> %s", npc.displayName, target.Name))
end

-- Unfollow Action
function ActionService.unfollow(npc)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s stopped following", npc.displayName))
    if npc then
        -- Delegate to MovementService to stop following
        movementServiceInstance:stopFollowing(npc)
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
        movementServiceInstance:moveNPCToPosition(npc, position)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Position provided for moveTo action")
    end
end

return ActionService