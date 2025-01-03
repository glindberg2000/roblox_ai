local AnimationManager = {}
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Add EMOTE_ANIMATIONS at the top level
local EMOTE_ANIMATIONS = {
    wave = "rbxassetid://507770239",
    laugh = "rbxassetid://507770818",
    dance = "rbxassetid://507771019",
    cheer = "rbxassetid://507770677",
    point = "rbxassetid://507770453",
    sit = "rbxassetid://507770840"
}

-- Different animation IDs for R6 and R15
local animations = {
    R6 = {
        idle = "rbxassetid://180435571",    -- R6 idle
        walk = "rbxassetid://180426354",    -- R6 walk
        run = "rbxassetid://180426354"      -- R6 run (same as walk but faster)
    },
    R15 = {
        idle = "rbxassetid://507766666",    -- R15 idle
        walk = "rbxassetid://507777826",    -- R15 walk
        run = "rbxassetid://507767714"      -- R15 run
    }
}

-- Table to store current animations per humanoid
local currentAnimations = {}

-- Add this helper function at the top
local function isMoving(humanoid)
    -- Check if the humanoid is actually moving by looking at velocity
    local rootPart = humanoid.Parent and humanoid.Parent:FindFirstChild("HumanoidRootPart")
    if rootPart then
        -- Use velocity magnitude to determine if actually moving
        return rootPart.Velocity.Magnitude > 0.1
    end
    return false
end

function AnimationManager:getRigType(humanoid)
    if not humanoid then return nil end
    
    local character = humanoid.Parent
    if character then
        if character:FindFirstChild("UpperTorso") then
            return "R15"
        else
            return "R6"
        end
    end
    return nil
end

function AnimationManager:applyAnimations(humanoid)
    if not humanoid then
        LoggerService:error("ANIMATION", "Cannot apply animations: Humanoid is nil")
        return
    end
    
    local rigType = self:getRigType(humanoid)
    if not rigType then
        LoggerService:error("ANIMATION", string.format("Cannot determine rig type for humanoid: %s", 
            humanoid.Parent and humanoid.Parent.Name or "unknown"))
        return
    end
    
    LoggerService:debug("ANIMATION", string.format("Detected %s rig for %s", 
        rigType, humanoid.Parent.Name))
    
    -- Get or create animator
    local animator = humanoid:FindFirstChild("Animator")
    if not animator then
        animator = Instance.new("Animator")
        animator.Parent = humanoid
    end
    
    -- Initialize animations table for this humanoid
    if not currentAnimations[humanoid] then
        currentAnimations[humanoid] = {
            rigType = rigType,
            tracks = {}
        }
    end
    
    -- Preload all animations for this rig type
    for name, id in pairs(animations[rigType]) do
        local animation = Instance.new("Animation")
        animation.AnimationId = id
        local track = animator:LoadAnimation(animation)
        currentAnimations[humanoid].tracks[name] = track
        LoggerService:debug("ANIMATION", string.format("Loaded %s animation for %s (%s)", 
            name, humanoid.Parent.Name, rigType))
    end
    
    -- Connect to state changes for animation updates
    humanoid.StateChanged:Connect(function(_, new_state)
        if (new_state == Enum.HumanoidStateType.Running or 
            new_state == Enum.HumanoidStateType.Walking) and 
            isMoving(humanoid) then
            -- Only play walk/run if actually moving
            local speed = humanoid.WalkSpeed
            self:playAnimation(humanoid, speed > 8 and "run" or "walk")
        else
            -- Play idle for any other state or when not moving
            self:playAnimation(humanoid, "idle")
        end
    end)
    
    -- Also connect to physics updates to catch movement changes
    local rootPart = humanoid.Parent and humanoid.Parent:FindFirstChild("HumanoidRootPart")
    if rootPart then
        game:GetService("RunService").Heartbeat:Connect(function()
            if humanoid.Parent and not humanoid.Parent.Parent then return end -- Check if destroyed
            
            if isMoving(humanoid) then
                local speed = humanoid.WalkSpeed
                self:playAnimation(humanoid, speed > 8 and "run" or "walk")
            else
                self:playAnimation(humanoid, "idle")
            end
        end)
    end
    
    -- Start with idle animation
    self:playAnimation(humanoid, "idle")
end

function AnimationManager:playAnimation(humanoid, animationName)
    if not humanoid or not currentAnimations[humanoid] then return end
    
    local animData = currentAnimations[humanoid]
    local track = animData.tracks and animData.tracks[animationName]
    
    if not track then
        LoggerService:error("ANIMATION", string.format("No %s animation track found for %s", 
            animationName, humanoid.Parent.Name))
        return
    end
    
    -- Stop other animations
    for name, otherTrack in pairs(animData.tracks) do
        if name ~= animationName and otherTrack.IsPlaying then
            otherTrack:Stop()
        end
    end
    
    -- Play the requested animation if it's not already playing
    if not track.IsPlaying then
        -- Adjust speed for running
        if animationName == "walk" and humanoid.WalkSpeed > 8 then
            track:AdjustSpeed(1.5)  -- Speed up walk animation for running
        else
            track:AdjustSpeed(1.0)  -- Normal speed for other animations
        end
        
        track:Play()
        LoggerService:debug("ANIMATION", string.format("Playing %s animation for %s", 
            animationName, humanoid.Parent.Name))
    end
end

function AnimationManager:stopAnimations(humanoid)
    if currentAnimations[humanoid] and currentAnimations[humanoid].tracks then
        for _, track in pairs(currentAnimations[humanoid].tracks) do
            track:Stop()
        end
        LoggerService:debug("ANIMATION", string.format("Stopped all animations for %s", 
            humanoid.Parent.Name))
    end
end

function AnimationManager:playEmote(humanoid, emoteType)
    -- Debug humanoid state
    LoggerService:debug("ANIMATION", string.format(
        "Humanoid state: RigType=%s, Animator=%s",
        humanoid.RigType.Name,
        humanoid:FindFirstChild("Animator") and "Found" or "Missing"
    ))

    -- Check if emote exists
    if not EMOTE_ANIMATIONS[emoteType] then
        LoggerService:error("ANIMATION", "Unknown emote type: " .. tostring(emoteType))
        return false
    end

    -- Create and load animation
    local animation = Instance.new("Animation")
    animation.AnimationId = EMOTE_ANIMATIONS[emoteType]
    
    -- Get or create Animator
    local animator = humanoid:FindFirstChild("Animator")
    if not animator then
        animator = Instance.new("Animator")
        animator.Parent = humanoid
        LoggerService:debug("ANIMATION", "Created new Animator")
    end
    
    -- Load and play with error checking
    local success, result = pcall(function()
        local track = animator:LoadAnimation(animation)
        LoggerService:debug("ANIMATION", "Successfully loaded animation")
        track:Play()
        LoggerService:debug("ANIMATION", "Started playing animation")
        return track
    end)

    if not success then
        LoggerService:error("ANIMATION", "Animation error: " .. tostring(result))
        return false
    end

    return true
end

return AnimationManager