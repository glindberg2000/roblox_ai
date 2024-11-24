-- WalkScript.server.lua
local WalkScript = {}

function WalkScript.walkToRandomPoint(npc)
    local humanoid = npc:FindFirstChildOfClass("Humanoid")
    if not humanoid then return end

    local currentPosition = npc.PrimaryPart.Position
    local randomOffset = Vector3.new(math.random(-20, 20), 0, math.random(-20, 20))
    local targetPosition = currentPosition + randomOffset

    humanoid:MoveTo(targetPosition)
    print(npc.Name .. " is walking to:", targetPosition)
end

return WalkScript