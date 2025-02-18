local BehaviorService = {}
BehaviorService.__index = BehaviorService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")  -- Changed to use built-in service
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local MovementService = require(ReplicatedStorage.Shared.NPCSystem.services.MovementService).new()

-- Updated Priority levels for behaviors
-- The hierarchy is as follows:
-- HUNT: Highest priority; all lower behaviors are disabled during a hunt.
-- NAVIGATE: Active when moving to a target and not hunting.
-- PATROL: For routine movements when no higher-priority action is active.
-- IDLE: Default fallback state.
-- FACE: Lowest priority; used for facing the participant during interactions.
local BEHAVIOR_PRIORITIES = {
    HUNT = 100,      -- Highest priority; all lower behaviors are disabled during a hunt.
    NAVIGATE = 80,   -- When not hunting, use navigation actions
    PATROL = 60,     -- Patrol behavior is active in routine scenarios
    IDLE = 40,       -- Default state when no other actions are active
    FACE = 20       -- Used during interactions; lowest priority
}

function BehaviorService.new()
    local self = setmetatable({}, BehaviorService)
    self.currentBehaviors = {} -- Track current behavior per NPC
    return self
end

function BehaviorService:clearBehavior(npc)
    if not npc then return end
    
    LoggerService:debug("BEHAVIOR", string.format(
        "Clearing current behavior for NPC %s",
        npc.displayName
    ))
    
    -- Clean up current behavior if it exists
    if self.currentBehaviors[npc] and self.currentBehaviors[npc].cleanup then
        self.currentBehaviors[npc].cleanup()
    end
    
    self.currentBehaviors[npc] = nil
end

function BehaviorService:getCurrentBehavior(npc)
    if not npc then return nil end
    return self.currentBehaviors[npc] and self.currentBehaviors[npc].type
end

function BehaviorService:setBehavior(npc, behaviorType, params)
    if not npc or not npc.model then return end
    
    -- Convert behavior type to uppercase for consistency
    behaviorType = string.upper(behaviorType)
    
    -- Get current behavior priority
    local currentBehavior = self.currentBehaviors[npc]
    local currentPriority = currentBehavior and BEHAVIOR_PRIORITIES[currentBehavior.type] or 0
    
    -- Get new behavior priority
    local newPriority = BEHAVIOR_PRIORITIES[behaviorType] or 0
    
    -- Only change behavior if new priority is higher
    if newPriority < currentPriority then
        LoggerService:debug("BEHAVIOR", string.format(
            "Skipping behavior change for NPC %s: %s (priority %d) -> %s (priority %d)",
            npc.displayName,
            currentBehavior and currentBehavior.type or "NONE",
            currentPriority,
            behaviorType,
            newPriority
        ))
        return false
    end
    
    -- Clear any existing behavior
    self:clearBehavior(npc)
    
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
    
    -- Initialize new behavior
    local behavior = {
        type = behaviorType,
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
        
        -- Store the thread for cleanup
        table.insert(cleanup, faceThread)
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
    
    -- Return a cleanup function that cancels all threads
    return function()
        for _, thread in ipairs(cleanup) do
            task.cancel(thread)
        end
        -- Reset orientation to forward
        if npc.model and npc.model:FindFirstChild("HumanoidRootPart") then
            npc.model.HumanoidRootPart.CFrame = CFrame.new(
                npc.model.HumanoidRootPart.Position,
                npc.model.HumanoidRootPart.Position + npc.model.HumanoidRootPart.CFrame.LookVector
            )
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

-- Add a new function to handle concurrent behaviors
function BehaviorService:executeSecondaryBehavior(npc, behaviorType, params)
    if not npc or not npc.model then return end
    
    -- Convert behavior type to uppercase for consistency
    behaviorType = string.upper(behaviorType)
    
    -- Get current behavior
    local currentBehavior = self.currentBehaviors[npc]
    if not currentBehavior then return false end
    
    -- List of behaviors that can run concurrently with others
    local CONCURRENT_BEHAVIORS = {
        EMOTE = true,
        FACE = true
    }
    
    if not CONCURRENT_BEHAVIORS[behaviorType] then
        LoggerService:debug("BEHAVIOR", string.format(
            "Cannot run non-concurrent behavior %s while %s is active",
            behaviorType,
            currentBehavior.type
        ))
        return false
    end
    
    -- Execute the concurrent behavior
    if behaviorType == "EMOTE" then
        local AnimationService = require(ReplicatedStorage.Shared.NPCSystem.services.AnimationService)
        
        -- If we need to face a target while emoting
        if params.target then
            local targetPlayer = game.Players:FindFirstChild(params.target)
            if targetPlayer and targetPlayer.Character then
                local targetPos = targetPlayer.Character.HumanoidRootPart.Position
                local npcPos = npc.model.HumanoidRootPart.Position
                
                -- Keep Y position the same to avoid tilting
                targetPos = Vector3.new(targetPos.X, npcPos.Y, targetPos.Z)
                
                -- Face target temporarily
                npc.model.HumanoidRootPart.CFrame = CFrame.lookAt(
                    npcPos,
                    targetPos
                )
                
                -- Return to original orientation after emote
                task.delay(2, function()
                    if currentBehavior.type == "PATROL" then
                        -- Reset to patrol orientation
                        local lookVector = npc.model.HumanoidRootPart.CFrame.LookVector
                        npc.model.HumanoidRootPart.CFrame = CFrame.new(
                            npc.model.HumanoidRootPart.Position,
                            npc.model.HumanoidRootPart.Position + lookVector
                        )
                    end
                end)
            end
        end
        
        -- Play the emote animation
        return AnimationService:playEmote(npc.model.Humanoid, params.type)
    end
    
    return true
end

return BehaviorService 