-- AnimateScript.server.lua
local AnimateScript = {}

function AnimateScript.applyTo(npcModel)
    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    if not humanoid then
        warn("No Humanoid found in model:", npcModel.Name)
        return
    end

    -- Attach an Animator if not present
    local animator = humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", humanoid)

    -- Add animations (these IDs must be your actual animation assets)
    local animations = {
        walk = "rbxassetid://180426354",  -- Replace with your walk animation asset ID
        jump = "rbxassetid://125750702",  -- Replace with your run animation asset ID
    }

    -- Create Animation objects for each animation
    for animName, assetId in pairs(animations) do
        local anim = Instance.new("Animation")
        anim.Name = animName
        anim.AnimationId = assetId
        anim.Parent = npcModel

        local track = animator:LoadAnimation(anim)
        npcModel:SetAttribute(animName .. "Track", track)
    end

    print("Animations applied to:", npcModel.Name)
end

return AnimateScript