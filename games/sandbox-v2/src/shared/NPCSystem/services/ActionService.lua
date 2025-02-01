local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local NPCManagerV3 = require(ReplicatedStorage.Shared.NPCSystem.NPCManagerV3)
local NavigationService = require(ReplicatedStorage.Shared.NPCSystem.services.NavigationService)
local movementServiceInstance = NPCManagerV3.getInstance().movementService
local AnimationService = require(ReplicatedStorage.Shared.NPCSystem.services.AnimationService)

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

function ActionService.navigate(npc, destination)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s navigate request", npc.displayName))

    -- If currently following, stop first
    if npc.isFollowing then
        ActionService.unfollow(npc)
    end

    -- Check if we have coordinates in the destination
    if type(destination) == "table" and destination.coordinates then
        LoggerService:debug("ACTION_SERVICE", string.format(
            "NPC %s navigating to coordinates: %d, %d, %d",
            npc.displayName,
            destination.coordinates.x,
            destination.coordinates.y,
            destination.coordinates.z
        ))
        return NavigationService:Navigate(npc, nil, destination.coordinates)
    end

    LoggerService:warn("ACTION_SERVICE", "No coordinates provided for navigation")
    return false
end

-- Add emote handling
function ActionService.emote(npc, emoteData)
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

return ActionService