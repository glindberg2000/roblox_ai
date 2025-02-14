local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local NPCManagerV3 = require(ReplicatedStorage.Shared.NPCSystem.NPCManagerV3)
local NavigationService = require(ReplicatedStorage.Shared.NPCSystem.services.NavigationService)
local movementServiceInstance = NPCManagerV3.getInstance().movementService
local AnimationService = require(ReplicatedStorage.Shared.NPCSystem.services.AnimationService)
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local BehaviorService = require(ReplicatedStorage.Shared.NPCSystem.services.BehaviorService).new()
local PatrolService = require(ReplicatedStorage.Shared.NPCSystem.services.PatrolService)

local ActionService = {}
ActionService.__index = ActionService

-- Priority levels for behaviors
local BEHAVIOR_PRIORITIES = {
    EMERGENCY = 100,  -- hide, flee
    NAVIGATION = 80,  -- navigate_to
    FOLLOWING = 60,   -- follow commands
    PATROL = 40,      -- patrol routes
    WANDER = 20,      -- casual wandering
    IDLE = 0         -- default state
}

function ActionService.new()
    return setmetatable({}, ActionService)
end

function ActionService:handleAction(npc, actionData)
    if not npc or not actionData then 
        LoggerService:warn("ACTION", "Invalid action data or NPC")
        return false 
    end
    
    LoggerService:debug("ACTION", string.format(
        "Received action data: %s",
        HttpService:JSONEncode(actionData)
    ))
    
    -- Handle both direct action and wrapped actions array format
    local actions = actionData.actions or {actionData}
    
    for _, action in ipairs(actions) do
        -- Validate standardized format
        if not action.type or not action.data then
            LoggerService:warn("ACTION", "Invalid action format - missing type or data")
            continue
        end
        
        LoggerService:debug("ACTION", string.format(
            "Processing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(action)
        ))
        
        -- Update NPC status with action message if provided
        if action.message then
            npc.currentAction = action.message
        end

        -- Map API actions to behaviors
        if action.type == "hunt" then
            return self:hunt(npc, action.data)
        elseif action.type == "patrol" then
            return self:patrol(npc, action.data)
        elseif action.type == "run" then
            return self:run(npc, action.data)
        elseif action.type == "jump" then
            return self:jump(npc)
        elseif action.type == "idle" then
            return BehaviorService:setBehavior(npc, "idle", {
                allowWander = false,  -- Don't wander when specifically idle
                target = action.target
            })
            
        elseif action.type == "wander" then
            return BehaviorService:setBehavior(npc, "idle", {
                allowWander = true,
                wanderRadius = 40,
                wanderArea = action.target -- Optional area constraint
            })
            
        elseif action.type == "follow" then
            local target = Players:FindFirstChild(action.target)
            if not target then return false end
            
            return BehaviorService:setBehavior(npc, "follow", {
                target = target
            })
            
        elseif action.type == "unfollow" then
            return BehaviorService:setBehavior(npc, "idle", {
                allowWander = false
            })
            
        elseif action.type == "hide" then
            return BehaviorService:setBehavior(npc, "hide", {
                coverLocation = action.target
            })
            
        elseif action.type == "flee" then
            return BehaviorService:setBehavior(npc, "flee", {
                threat = action.target
            })
            
        elseif action.type == "emote" then
            -- Handle emotes through AnimationService
            local AnimationService = require(ReplicatedStorage.Shared.NPCSystem.services.AnimationService)
            local emoteTarget = Players:FindFirstChild(action.target)
            
            -- Play emote and face target if specified
            if emoteTarget then
                BehaviorService:setBehavior(npc, "idle", {
                    target = action.target,
                    allowWander = false
                })
            end
            
            return AnimationService:playEmote(npc.model.Humanoid, action.type)
        end
    end
    
    return false
end

-- Helper function to get patrol points for an area
function ActionService:getPatrolPoints(areaName)
    -- TODO: Implement area-specific patrol points
    -- For now return some default points around current position
    return {}
end

function ActionService:setBehavior(npc, behaviorType, params)
    if not npc then return end
    
    -- Get current behavior priority
    local currentPriority = 0
    if self.currentBehaviors[npc] then
        currentPriority = BEHAVIOR_PRIORITIES[self.currentBehaviors[npc].type] or 0
    end
    
    -- Get new behavior priority
    local newPriority = BEHAVIOR_PRIORITIES[behaviorType] or 0
    
    -- Only change behavior if new priority is higher or current behavior is done
    if newPriority >= currentPriority then
        -- Clean up current behavior if it exists
        if self.currentBehaviors[npc] and self.currentBehaviors[npc].cleanup then
            self.currentBehaviors[npc].cleanup()
        end
        
        -- Set up new behavior
        local behavior = {
            type = behaviorType,
            params = params,
            startTime = os.time()
        }
        
        -- Initialize behavior-specific logic
        if behaviorType == "patrol" then
            behavior.cleanup = self:initializePatrol(npc, params)
        elseif behaviorType == "wander" then
            behavior.cleanup = self:initializeWander(npc, params)
        elseif behaviorType == "hide" then
            behavior.cleanup = self:initializeHide(npc, params)
        elseif behaviorType == "flee" then
            behavior.cleanup = self:initializeFlee(npc, params)
        elseif behaviorType == "follow" then
            behavior.cleanup = self:initializeFollow(npc, params)
        end
        
        self.currentBehaviors[npc] = behavior
        
        -- Update NPC status
        npc:updateStatus({
            current_action = behaviorType,
            target = params and params.target,
            style = params and params.style
        })
        
        return true
    end
    
    return false
end

-- Behavior initialization functions
function ActionService:initializePatrol(npc, params)
    -- Set up patrol route and movement
    local MovementService = require(script.Parent.MovementService)
    local movement = MovementService.new()
    
    -- Start patrol loop
    local patrolThread = task.spawn(function()
        while true do
            if params.target then
                movement:moveNPCToPosition(npc, params.target)
            end
            task.wait(1)
        end
    end)
    
    -- Return cleanup function
    return function()
        task.cancel(patrolThread)
    end
end

-- Add other behavior initializations (wander, hide, flee, follow)
-- Similar structure to patrol but with behavior-specific logic

function ActionService.follow(npc, action)
    -- Debug log the entire action
    LoggerService:debug("ACTION_SERVICE", string.format(
        "Follow action data: %s",
        typeof(action) == "string" and action or HttpService:JSONEncode(action)
    ))

    -- If action is a string (JSON), decode it
    if typeof(action) == "string" then
        local success, decoded = pcall(function()
            return HttpService:JSONDecode(action)
        end)
        if success then
            action = decoded
        else
            LoggerService:warn("ACTION_SERVICE", "Failed to decode action JSON")
            return
        end
    end

    -- Extract target from action data
    local targetName = action and (
        -- Try both formats
        (action.data and action.data.target) or  -- New format
        action.target                            -- Old format
    )
    
    LoggerService:debug("ACTION_SERVICE", string.format(
        "Extracted target name: %s (type: %s)",
        tostring(targetName),
        typeof(targetName)
    ))

    if not targetName then
        LoggerService:warn("ACTION_SERVICE", string.format(
            "No target specified for NPC %s to follow. Action data: %s",
            npc.displayName,
            typeof(action) == "string" and action or HttpService:JSONEncode(action)
        ))
        return
    end

    local target = Players:FindFirstChild(targetName)
    if not target then
        LoggerService:warn("ACTION_SERVICE", string.format(
            "Could not find player %s for NPC %s to follow",
            targetName,
            npc.displayName
        ))
        return
    end

    -- Now we have a valid target, set up following
    npc.isFollowing = true
    npc.followTarget = target
    npc.followStartTime = tick()
    npc.isWalking = false

    movementServiceInstance:startFollowing(npc, target.Character, {
        distance = 5,
        updateRate = 0.1
    })

    LoggerService:debug("ACTION_SERVICE", string.format(
        "NPC %s follow state set -> %s",
        npc.displayName,
        target.Name
    ))
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

function ActionService.navigate(npc, destination)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s navigate request", npc.displayName))

    -- If currently following, stop first
    if npc.isFollowing then
        ActionService.unfollow(npc)
    end

    -- Check if we have coordinates in the destination
    if type(destination) == "table" then
        if destination.coordinates then
            local coords = destination.coordinates
            LoggerService:debug("ACTION_SERVICE", string.format(
                "NPC %s navigating to coordinates: %.0f, %.0f, %.0f",
                npc.displayName,
                coords.x,
                coords.y,
                coords.z
            ))
            
            -- Convert coordinates table to Vector3
            local targetPosition = Vector3.new(
                coords.x,
                coords.y,
                coords.z
            )
            
            return NavigationService:Navigate(npc, targetPosition)
        elseif destination.destination_slug then
            LoggerService:debug("ACTION_SERVICE", string.format(
                "NPC %s navigating to location: %s",
                npc.displayName,
                destination.destination_slug
            ))
            
            return NavigationService:Navigate(npc, destination.destination_slug)
        end
    end

    LoggerService:warn("ACTION_SERVICE", "Invalid navigation data format")
    return false
end

-- Add emote handling
function ActionService.emote(npc, action)
    -- Debug log the entire action
    LoggerService:debug("ACTION_SERVICE", string.format(
        "Emote action data: %s",
        typeof(action) == "string" and action or HttpService:JSONEncode(action)
    ))

    -- If action is a string (JSON), decode it
    if typeof(action) == "string" then
        local success, decoded = pcall(function()
            return HttpService:JSONDecode(action)
        end)
        if success then
            action = decoded
        else
            LoggerService:warn("ACTION_SERVICE", "Failed to decode emote action JSON")
            return false
        end
    end

    -- Extract emote data from action
    local emoteData = action.data or action  -- Try both formats
    if not emoteData or not emoteData.emote_type then
        LoggerService:warn("ACTION_SERVICE", string.format(
            "Invalid emote data for NPC %s: %s",
            npc.displayName,
            HttpService:JSONEncode(action)
        ))
        return false
    end

    LoggerService:debug("ACTION_SERVICE", string.format(
        "NPC %s performing emote: %s", 
        npc.displayName,
        emoteData.emote_type
    ))

    -- Debug NPC model structure
    if not npc.model then
        LoggerService:error("ACTION_SERVICE", "No model found for NPC")
        return false
    end

    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then
        LoggerService:error("ACTION_SERVICE", "No humanoid found in NPC model")
        return false
    end

    -- Check if model is R6 or R15
    local isR15 = npc.model:FindFirstChild("UpperTorso") ~= nil
    LoggerService:debug("ACTION_SERVICE", string.format(
        "NPC %s is using %s rig",
        npc.displayName,
        isR15 and "R15" or "R6"
    ))

    -- Use simpler R6 animations if needed
    local R6_EMOTES = {
        wave = "rbxassetid://128777973",  -- Basic R6 wave
        laugh = "rbxassetid://129423131", -- Basic R6 laugh
        dance = "rbxassetid://182435998", -- Basic R6 dance
        cheer = "rbxassetid://129423030", -- Basic R6 cheer
        point = "rbxassetid://128853357", -- Basic R6 point
        sit = "rbxassetid://178130996"    -- Basic R6 sit
    }

    -- Choose animation based on rig type
    local animationId = isR15 and EMOTE_ANIMATIONS[emoteData.emote_type] or R6_EMOTES[emoteData.emote_type]
    if not animationId then
        LoggerService:error("ACTION_SERVICE", "No animation found for emote type: " .. emoteData.emote_type)
        return false
    end

    -- Create and play animation
    local animation = Instance.new("Animation")
    animation.AnimationId = animationId
    
    local animator = humanoid:FindFirstChild("Animator")
    if not animator then
        animator = Instance.new("Animator")
        animator.Parent = humanoid
    end

    local track = animator:LoadAnimation(animation)
    track:Play()

    return true
end

function NPCManagerV3:executeAction(npc, player, action)
    if action.type == "follow" then
        if USE_ACTION_SERVICE then
            local target = action.data and action.data.target
            LoggerService:debug("ACTION", string.format(
                "Using ActionService to handle 'follow' with target: %s",
                target or "nil"
            ))
            ActionService.follow(npc, action)  -- Pass the whole action object
        else
            LoggerService:debug("ACTION", "Using LEGACY 'startFollowing' method for 'follow'")
            self:startFollowing(npc, player)
        end
    end
end

function ActionService.patrol(npc, action)
    LoggerService:debug("ACTION_SERVICE", string.format(
        "NPC %s patrol request",
        npc.displayName
    ))
    
    -- If currently following, stop first
    if npc.isFollowing then
        ActionService.unfollow(npc)
    end
    
    -- Handle case where location is incorrectly in type field
    local area = action.target ~= "" and action.target or action.type
    local style = "normal"  -- Default patrol style
    
    if not area then
        warn("Missing patrol location in action data")
        return
    end
    
    LoggerService:debug("PATROL", string.format(
        "Starting patrol for NPC %s with area: %s, style: %s",
        npc.displayName, tostring(area), tostring(style)
    ))
    
    return PatrolService:startPatrol(npc, {
        type = area,  -- Should be "full" here
        target = ""   -- Empty for full patrol
    })
end

function ActionService:hunt(npc, data)
    if not data then
        LoggerService:warn("ACTION", "No data provided for hunt action")
        return false
    end

    LoggerService:debug("ACTION", string.format(
        "Hunt called with data: %s",
        HttpService:JSONEncode(data)
    ))

    -- Extract target from data, handling both formats
    local targetName = data.target or (data.data and data.data.target)
    
    if not targetName then
        LoggerService:warn("ACTION", "No target specified for hunt action")
        return false
    end
    
    LoggerService:debug("ACTION", string.format(
        "Looking for target: %s",
        targetName
    ))
    
    -- Try to find target (player or NPC)
    local target
    
    -- First check if target is a player
    target = Players:FindFirstChild(targetName)
    if target then
        LoggerService:debug("ACTION", string.format(
            "Found player target: %s",
            target.Name
        ))
    end
    
    -- If not a player, check if it's an NPC
    if not target then
        local npcManager = NPCManagerV3.getInstance()
        LoggerService:debug("ACTION", "Searching NPCs for target")
        for _, npcInstance in pairs(npcManager.npcs) do
            LoggerService:debug("ACTION", string.format(
                "Checking NPC: %s",
                npcInstance.displayName
            ))
            if npcInstance.displayName == targetName then
                target = npcInstance
                LoggerService:debug("ACTION", "Found NPC target")
                break
            end
        end
    end
    
    if not target then
        LoggerService:warn("ACTION", string.format(
            "Could not find target (player or NPC): %s",
            targetName
        ))
        return false
    end
    
    -- Update NPC status to show they're hunting
    npc.currentAction = string.format("Hunting %s", targetName)
    
    -- Start the hunt behavior
    local huntType = (data.type or data.data and data.data.type) or "track"
    local success = NavigationService:CombatNavigate(npc, target, huntType)
    if not success then
        LoggerService:warn("ACTION", string.format(
            "Hunt navigation failed for NPC %s targeting %s",
            npc.displayName,
            targetName
        ))
        npc.currentAction = "Idle"
    end
    
    return success
end

return ActionService