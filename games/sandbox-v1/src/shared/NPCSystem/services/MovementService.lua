-- MovementService.lua
local MovementService = {}

function MovementService:moveNPCToPosition(npc, targetPosition)
    if not npc or not npc.model then return end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then return end
    
    -- Get current position
    local currentPosition = npc.model:GetPrimaryPartCFrame().Position
    local distance = (targetPosition - currentPosition).Magnitude
    
    -- Set appropriate walk speed
    if distance > 20 then
        humanoid.WalkSpeed = 16  -- Run speed
    else
        humanoid.WalkSpeed = 8   -- Walk speed
    end
    
    -- Move to position
    humanoid:MoveTo(targetPosition)
end

function MovementService:getRandomPosition(center, radius)
    local angle = math.random() * math.pi * 2
    local distance = math.sqrt(math.random()) * radius
    
    return Vector3.new(
        center.X + math.cos(angle) * distance,
        center.Y,
        center.Z + math.sin(angle) * distance
    )
end

return MovementService 