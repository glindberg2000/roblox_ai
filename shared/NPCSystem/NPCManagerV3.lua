local AnimationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.AnimationService)

-- ... existing code ... 

-- Example usage of AnimationService
function NPCManagerV3:initializeNPC(npc)
    local humanoid = npc:FindFirstChildOfClass("Humanoid")
    if humanoid then
        AnimationService:applyAnimations(humanoid)
    end
end

-- Move playEmote to AnimationService if needed
function NPCManagerV3:playEmote(npc, emoteName)
    AnimationService:playEmote(npc, emoteName)
end