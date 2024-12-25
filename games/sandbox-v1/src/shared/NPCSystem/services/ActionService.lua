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

local NavigationService = require(ReplicatedStorage.Shared.NPCSystem.services.NavigationService)

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

function ActionService:handleNavigate(npc, data)
    LoggerService:debug("ACTION_SERVICE", string.format(
        "NPC %s navigate request: %s", 
        npc.displayName, 
        data.destination
    ))
    
    -- Check if NPC can move
    if npc.isMovementLocked then
        LoggerService:warn("NAVIGATION", string.format(
            "NPC %s movement is locked - cannot navigate",
            npc.displayName
        ))
        return false
    end
    
    -- Use coordinates directly if provided
    if data.coordinates then
        local targetPos = Vector3.new(
            data.coordinates.x,
            data.coordinates.y,
            data.coordinates.z
        )
        
        LoggerService:debug("NAVIGATION", string.format(
            "Moving %s to coordinates: (%.1f, %.1f, %.1f)",
            npc.displayName,
            targetPos.X, targetPos.Y, targetPos.Z
        ))
        
        -- Use MovementService to handle actual movement
        self.movementService:moveNPCToPosition(npc, targetPos)
        return true
    end
    
    LoggerService:warn("NAVIGATION", string.format(
        "No valid coordinates for %s navigation",
        npc.displayName
    ))
    return false
end

return ActionService