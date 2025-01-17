local ActionRouter = {}

local ActionHandlers = {}
local ActionService = require(ReplicatedStorage.Shared.NPCSystem.services.ActionService)

-- Function to register action handlers
function ActionRouter:registerAction(actionType, handler)
    ActionHandlers[actionType] = handler
end

-- Function to route actions to the correct handler
function ActionRouter:routeAction(npc, participant, action)
    local actionType = action and action.type

    if not actionType then
        warn("[ActionRouter] Invalid action format:", action)
        return
    end

    local handler = ActionHandlers[actionType]
    if handler then
        print("[ActionRouter] Executing action:", actionType)
        handler(npc, participant, action.data)
    else
        warn("[ActionRouter] No handler registered for action:", actionType)
    end
end

-- Initialize action handlers
function ActionRouter:initialize()
    -- Register a "follow" action
    self:registerAction("follow", function(npc, participant, data)
        local target = participant -- Assuming the participant is the follow target
        ActionService.follow(npc, target, data)
    end)

    -- Register an "unfollow" action
    self:registerAction("unfollow", function(npc, _, _)
        ActionService.unfollow(npc)
    end)

    -- Register a "chat" action
    self:registerAction("chat", function(npc, _, data)
        if data.message then
            ActionService.chat(npc, data.message)
        else
            warn("[ActionRouter] Missing message for chat action")
        end
    end)
end

return ActionRouter