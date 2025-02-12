local BehaviorService = {}
BehaviorService.__index = BehaviorService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")  -- Changed to use built-in service
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local MovementService = require(ReplicatedStorage.Shared.NPCSystem.services.MovementService).new()

-- Priority levels for behaviors
local BEHAVIOR_PRIORITIES = {
    EMERGENCY = 100,  -- hide, flee
    CHAT = 90,       -- during conversations
    NAVIGATE = 80,   -- navigate_to
    FOLLOW = 60,     -- follow commands
    IDLE = 20       -- default state
}

function BehaviorService.new()
    local self = setmetatable({}, BehaviorService)
    self.currentBehaviors = {} -- Track current behavior per NPC
    return self
end

function BehaviorService:setBehavior(npc, behaviorType, params)
    if not npc or not npc.model then return end
    
    -- Safely encode params for logging
    local paramsString = ""
    pcall(function()
        paramsString = HttpService:JSONEncode(params or {})
    end)
    
    LoggerService:debug("BEHAVIOR", string.format(
        "Setting behavior %s for NPC %s with params: %s",
        behaviorType,
        npc.displayName,
        paramsString
    ))
    
    -- Clean up current behavior if it exists
    if self.currentBehaviors[npc] and self.currentBehaviors[npc].cleanup then
        self.currentBehaviors[npc].cleanup()
    end
    
    -- Initialize new behavior
    local behavior = {
        type = string.upper(behaviorType),
        params = params,
        startTime = os.time()
    }
    
    -- Set up behavior-specific logic
    if behaviorType == "idle" then
        behavior.cleanup = self:initializeIdle(npc, params)
    elseif behaviorType == "follow" then
        behavior.cleanup = self:initializeFollow(npc, params)
    elseif behaviorType == "navigate" then
        behavior.cleanup = self:initializeNavigate(npc, params)
    elseif behaviorType == "chat" then
        behavior.cleanup = self:initializeChat(npc, params)
    end
    
    self.currentBehaviors[npc] = behavior
    
    return true
end

-- Basic idle behavior with optional wandering and target facing
function BehaviorService:initializeIdle(npc, params)
    local cleanup = {}
    
    -- Stop any current movement
    if npc.model:FindFirstChild("Humanoid") then
        npc.model.Humanoid:MoveTo(npc.model.HumanoidRootPart.Position)
    end
    
    -- Set up target facing if target specified
    if params.target then
        LoggerService:debug("BEHAVIOR", string.format(
            "Setting up idle facing behavior for NPC %s targeting %s",
            npc.displayName,
            params.target
        ))

        local faceThread = task.spawn(function()
            while true do
                local targetPlayer = game.Players:FindFirstChild(params.target)
                if targetPlayer and targetPlayer.Character and targetPlayer.Character:FindFirstChild("HumanoidRootPart") then
                    -- Update NPC orientation to face target
                    local targetPos = targetPlayer.Character.HumanoidRootPart.Position
                    local npcPos = npc.model.HumanoidRootPart.Position
                    
                    -- Keep Y position the same to avoid tilting
                    targetPos = Vector3.new(targetPos.X, npcPos.Y, targetPos.Z)
                    
                    npc.model.HumanoidRootPart.CFrame = CFrame.lookAt(
                        npcPos,
                        targetPos
                    )
                end
                task.wait(0.1)
            end
        end)
        table.insert(cleanup, faceThread)
        
        -- Don't allow wandering when targeting
        return function()
            for _, thread in ipairs(cleanup) do
                task.cancel(thread)
            end
        end
    end
    
    -- Only set up wandering if no target
    if params.allowWander then
        local wanderThread = task.spawn(function()
            while true do
                task.wait(math.random(15, 30))
                if math.random() < 0.5 then
                    local targetPos = MovementService:getRandomPosition(
                        npc.model.HumanoidRootPart.Position,
                        params.wanderRadius or 40
                    )
                    MovementService:moveNPCToPosition(npc, targetPos)
                end
            end
        end)
        table.insert(cleanup, wanderThread)
    end
    
    return function()
        for _, thread in ipairs(cleanup) do
            task.cancel(thread)
        end
    end
end

-- Follow a target
function BehaviorService:initializeFollow(npc, params)
    if not params.target then return function() end end
    
    local followThread = MovementService:startFollowing(npc, params.target, {
        distance = params.distance or 5
    })
    
    return function()
        MovementService:stopFollowing(npc)
    end
end

-- Navigate to position
function BehaviorService:initializeNavigate(npc, params)
    if not params.position then return function() end end
    
    task.spawn(function()
        MovementService:moveNPCToPosition(npc, params.position)
    end)
    
    return function() end
end

-- Chat behavior (stops movement, faces target)
function BehaviorService:initializeChat(npc, params)
    if not params.target then return function() end end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        humanoid:MoveTo(npc.model.HumanoidRootPart.Position) -- Stop moving
    end
    
    -- Face target
    if params.target and params.target:FindFirstChild("HumanoidRootPart") then
        npc.model.HumanoidRootPart.CFrame = CFrame.lookAt(
            npc.model.HumanoidRootPart.Position,
            params.target.HumanoidRootPart.Position
        )
    end
    
    return function() end
end

return BehaviorService 