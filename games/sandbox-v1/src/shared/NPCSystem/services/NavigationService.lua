local NavigationService = {}
local PathfindingService = game:GetService("PathfindingService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Predefined destinations (can be moved to a config file later)
local Destinations = {
    town_center = Vector3.new(100, 10, 200),
    blacksmith = Vector3.new(-50, 10, 300),
    castle = Vector3.new(200, 10, -100),
    ["petes_merch_stand"] = Vector3.new(-10.289, 21.512, -127.797),
    ["merch_stand"] = Vector3.new(-10.289, 21.512, -127.797), -- Alias
    ["stand"] = Vector3.new(-10.289, 21.512, -127.797),       -- Another alias
    ["merch"] = Vector3.new(-10.289, 21.512, -127.797)        -- Another alias
}

function NavigationService:goToDestination(npc, destinationName)
    local destination = Destinations[destinationName]
    if not destination then
        LoggerService:warn("NAVIGATION", string.format("Unknown destination: %s", destinationName))
        return false
    end

    LoggerService:debug("NAVIGATION", string.format(
        "NPC %s navigating to %s at position (%0.1f, %0.1f, %0.1f)",
        npc.displayName,
        destinationName,
        destination.X,
        destination.Y,
        destination.Z
    ))

    -- Create path
    local path = PathfindingService:CreatePath({
        AgentRadius = 2,
        AgentHeight = 5,
        AgentCanJump = true
    })

    -- Compute path
    local success, errorMessage = pcall(function()
        path:ComputeAsync(npc.model.PrimaryPart.Position, destination)
    end)

    if not success then
        LoggerService:warn("NAVIGATION", string.format("Path computation failed: %s", errorMessage))
        return false
    end

    -- After path computation:
    if success then
        LoggerService:debug("NAVIGATION", string.format(
            "Path computed successfully for %s with %d waypoints",
            npc.displayName,
            #waypoints
        ))
    else
        LoggerService:warn("NAVIGATION", string.format(
            "Path computation failed for %s: %s",
            npc.displayName,
            errorMessage
        ))
        return false
    end

    -- Follow path
    local waypoints = path:GetWaypoints()
    for i, waypoint in ipairs(waypoints) do
        LoggerService:debug("NAVIGATION", string.format(
            "NPC %s moving to waypoint %d/%d at (%0.1f, %0.1f, %0.1f)",
            npc.displayName,
            i,
            #waypoints,
            waypoint.Position.X,
            waypoint.Position.Y,
            waypoint.Position.Z
        ))
        
        if not npc.model or not npc.model:FindFirstChild("Humanoid") then
            LoggerService:warn("NAVIGATION", string.format(
                "NPC %s or humanoid no longer exists during waypoint %d",
                npc.displayName,
                i
            ))
            return false
        end

        npc.model.Humanoid:MoveTo(waypoint.Position)
        npc.model.Humanoid.MoveToFinished:Wait()
    end

    LoggerService:debug("NAVIGATION", string.format(
        "NPC %s reached destination %s",
        npc.displayName,
        destinationName
    ))
    return true
end

return NavigationService 