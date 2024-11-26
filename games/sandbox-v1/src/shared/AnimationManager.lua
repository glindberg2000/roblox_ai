local AnimationManager = {}
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

local animations = {
    walk = "rbxassetid://180426354", -- Replace with your walk animation asset ID
    jump = "rbxassetid://125750702", -- Replace with your jump animation asset ID
    idle = "rbxassetid://507766388", -- Replace with your idle animation asset ID
}

-- Table to store animations per humanoid
local animationTracks = {}

-- Apply animations to NPC's humanoid
function AnimationManager:applyAnimations(humanoid)
    if not humanoid then
        Logger:log("ERROR", "Cannot apply animations: Humanoid is nil")
        return
    end

    local animator = humanoid:FindFirstChild("Animator") or Instance.new("Animator", humanoid)

    -- Initialize animationTracks for this humanoid
    animationTracks[humanoid] = {}

    -- Preload animations
    for name, id in pairs(animations) do
        local animation = Instance.new("Animation")
        animation.AnimationId = id

        local animationTrack = animator:LoadAnimation(animation)
        animationTracks[humanoid][name] = animationTrack
        Logger:log("ANIMATION", string.format("Loaded animation '%s' for humanoid: %s", 
            name, 
            humanoid.Parent.Name
        ))
    end

    Logger:log("ANIMATION", string.format("Animations applied to humanoid: %s", humanoid.Parent.Name))
end

-- Play a specific animation
function AnimationManager:playAnimation(humanoid, animationName)
    if animationTracks[humanoid] and animationTracks[humanoid][animationName] then
        Logger:log("ANIMATION", string.format("Playing animation '%s' for humanoid: %s", 
            animationName, 
            humanoid.Parent.Name
        ))
        animationTracks[humanoid][animationName]:Play()
    else
        Logger:log("ERROR", string.format("No animation track found: %s for humanoid: %s", 
            animationName, 
            humanoid and humanoid.Parent and humanoid.Parent.Name or "unknown"
        ))
    end
end

-- Stop all animations
function AnimationManager:stopAnimations(humanoid)
    if animationTracks[humanoid] then
        for name, track in pairs(animationTracks[humanoid]) do
            track:Stop()
            Logger:log("ANIMATION", string.format("Stopped animation '%s' for humanoid: %s", 
                name, 
                humanoid.Parent.Name
            ))
        end
    end
end

return AnimationManager