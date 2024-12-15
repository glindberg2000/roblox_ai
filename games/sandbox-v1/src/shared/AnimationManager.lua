local AnimationManager = {}

function AnimationManager.new()
    local self = {}
    
    function self:loadAnimation(humanoid, animationId)
        local animator = humanoid:FindFirstChild("Animator") or Instance.new("Animator", humanoid)
        local animation = Instance.new("Animation")
        animation.AnimationId = "rbxassetid://" .. animationId
        return animator:LoadAnimation(animation)
    end
    
    function self:playAnimation(humanoid, animationId)
        local anim = self:loadAnimation(humanoid, animationId)
        if anim then
            anim:Play()
            return anim
        end
        return nil
    end
    
    return self
end

return AnimationManager 