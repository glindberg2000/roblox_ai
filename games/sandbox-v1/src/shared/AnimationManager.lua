local AnimationManager = {}
local Logger = require(game:GetService("ServerScriptService"):WaitForChild("Logger"))

-- Different animation IDs for R6 and R15
local customAnimations = {
    R6 = {
        idle = 132989623409836,  -- Custom idle
        walk = 117532359621969,  -- Custom walk
        run = 113904732335196    -- Custom run
    },
    R15 = {
        idle = 132989623409836,  -- Custom idle
        walk = 117532359621969,  -- Custom walk
        run = 113904732335196    -- Custom run
    }
}

-- Default fallback animations
local defaultAnimations = {
    R6 = {
        idle = 180435571,    -- Default R6 idle
        walk = 180426354,    -- Default R6 walk
        run = 180426354     -- Default R6 run
    },
    R15 = {
        idle = 2510197257,   -- Default R15 idle
        walk = 2510198475,   -- Default R15 walk
        run = 2510198475    -- Default R15 run
    }
}

-- At the top, add emergency animations
local emergencyAnimations = {
    R6 = {
        idle = 180435571,    -- Basic R6 idle
        walk = 180426354,    -- Basic R6 walk
        run = 180426354     -- Basic R6 run
    },
    R15 = {
        idle = 2510197257,   -- Basic R15 idle
        walk = 2510198475,   -- Basic R15 walk
        run = 2510198475    -- Basic R15 run
    }
}

-- Table to store current animations per humanoid
local currentAnimations = {}

-- Add at the top with other variables
local ANIMATION_DEBOUNCE = 0.2  -- Seconds between animation changes
local lastAnimationChange = {}

-- Modify isMoving to be more stable
local function isMoving(humanoid)
    local rootPart = humanoid.Parent and humanoid.Parent:FindFirstChild("HumanoidRootPart")
    if rootPart then
        -- Use a higher threshold to prevent jitter
        return rootPart.Velocity.Magnitude > 0.5
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
        Logger:log("ERROR", "Cannot apply animations: Humanoid is nil")
        return
    end
    
    local rigType = self:getRigType(humanoid)
    if not rigType then
        Logger:log("ERROR", string.format("Cannot determine rig type for humanoid: %s", 
            humanoid.Parent and humanoid.Parent.Name or "unknown"))
        return
    end
    
    Logger:log("ANIMATION", string.format("Detected %s rig for %s", 
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
    local loadedAny = false
    for name, _ in pairs(customAnimations[rigType]) do
        local success, track = self:loadAnimation(animator, name, rigType)
        
        if success and track then
            currentAnimations[humanoid].tracks[name] = track
            loadedAny = true
            Logger:log("ANIMATION", string.format("Successfully loaded %s animation for %s (%s)", 
                name, humanoid.Parent.Name, rigType))
        else
            Logger:log("ERROR", string.format("Failed to load %s animation for %s", 
                name, humanoid.Parent.Name))
        end
    end
    
    -- If no animations loaded at all, try emergency defaults
    if not loadedAny then
        Logger:log("ERROR", string.format("No animations loaded for %s, trying emergency defaults", 
            humanoid.Parent.Name))
            
        for name, id in pairs(emergencyAnimations[rigType]) do
            local animation = Instance.new("Animation")
            animation.AnimationId = "rbxassetid://" .. tostring(id)
            
            local success, track = pcall(function()
                local t = animator:LoadAnimation(animation)
                -- Verify track loaded
                if t and t.IsLoaded then
                    return t
                end
                return nil
            end)
            
            if success and track then
                currentAnimations[humanoid].tracks[name] = track
                Logger:log("ANIMATION", string.format("Loaded emergency %s animation for %s", 
                    name, humanoid.Parent.Name))
                loadedAny = true
            else
                Logger:log("ERROR", string.format("Failed to load emergency %s animation for %s", 
                    name, humanoid.Parent.Name))
            end
        end
        
        -- If still no animations, log critical error
        if not loadedAny then
            Logger:log("ERROR", string.format("CRITICAL: No animations could be loaded for %s", 
                humanoid.Parent.Name))
        end
    end
    
    -- Connect to state changes for animation updates
    humanoid.StateChanged:Connect(function(_, new_state)
        if (new_state == Enum.HumanoidStateType.Running) then
            if isMoving(humanoid) then
                local speed = humanoid.WalkSpeed
                self:playAnimation(humanoid, speed > 8 and "run" or "walk")
            end
        else
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
    
    -- Check debounce
    local now = tick()
    if lastAnimationChange[humanoid] and 
       (now - lastAnimationChange[humanoid]) < ANIMATION_DEBOUNCE then
        return
    end
    
    local animData = currentAnimations[humanoid]
    local track = animData.tracks and animData.tracks[animationName]
    
    if not track then
        Logger:log("ERROR", string.format("No %s animation track found for %s", 
            animationName, humanoid.Parent.Name))
        return
    end
    
    -- Only change animation if it's different
    local currentTrack = animData.currentTrack
    if currentTrack == track and track.IsPlaying then
        return
    end
    
    -- Stop other animations
    for _, otherTrack in pairs(animData.tracks) do
        if otherTrack.IsPlaying then
            otherTrack:Stop()
        end
    end
    
    -- Play the requested animation
    track:AdjustSpeed(animationName == "walk" and humanoid.WalkSpeed > 8 and 1.5 or 1.0)
    track:Play()
    
    -- Update tracking
    animData.currentTrack = track
    lastAnimationChange[humanoid] = now
    
    Logger:log("ANIMATION", string.format("Playing %s animation for %s", 
        animationName, humanoid.Parent.Name))
end

function AnimationManager:stopAnimations(humanoid)
    if currentAnimations[humanoid] and currentAnimations[humanoid].tracks then
        for _, track in pairs(currentAnimations[humanoid].tracks) do
            track:Stop()
        end
        Logger:log("ANIMATION", string.format("Stopped all animations for %s", 
            humanoid.Parent.Name))
    end
end

local function tryLoadAnimation(animator, id)
    local animation = Instance.new("Animation")
    animation.AnimationId = "rbxassetid://" .. tostring(id)
    
    -- Add small delay to ensure animation is ready
    wait(0.1)
    
    local success, result = pcall(function()
        local track = animator:LoadAnimation(animation)
        -- Verify track is valid
        if track and track.Length > 0 then
            return track
        end
        return nil
    end)
    
    if success and result then
        return result
    end
    
    return nil
end

function AnimationManager:loadAnimation(animator, name, rigType)
    -- Try custom animation
    local track = tryLoadAnimation(animator, customAnimations[rigType][name])
    if track then
        Logger:log("ANIMATION", string.format("Loaded custom %s animation (Length: %.2f)", 
            name, track.Length))
        return true, track
    end
    
    -- Log the failure details
    Logger:log("DEBUG", string.format("Failed to load custom animation %s (ID: %s)", 
        name, customAnimations[rigType][name]))
        
    -- Try default animation
    track = tryLoadAnimation(animator, defaultAnimations[rigType][name])
    if track then
        Logger:log("ANIMATION", string.format("Loaded default %s animation (Length: %.2f)", 
            name, track.Length))
        return true, track
    end
    
    return false, nil
end

return AnimationManager