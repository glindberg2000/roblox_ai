local NavigationService = {}
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Keep existing locations for backwards compatibility
local LOCATIONS = {
    Stand = Vector3.new(0, 0, 0),
    -- ... other locations
}

function NavigationService:goToDestination(npc, destination)
    -- Keep existing destination-based navigation
    if not LOCATIONS[destination] then
        LoggerService:warn("NAVIGATION", string.format("Unknown destination: %s", destination))
        return false
    end
    
    local targetPosition = LOCATIONS[destination]
    -- ... rest of existing destination logic
end

function NavigationService:NavigateToCoordinates(npc, coordinates)
    LoggerService:debug("NAVIGATION", string.format(
        "Attempting to navigate %s to coordinates: %d, %d, %d",
        npc.displayName,
        coordinates.x,
        coordinates.y,
        coordinates.z
    ))

    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then
        LoggerService:warn("NAVIGATION", "No humanoid found for NPC")
        return false
    end

    -- Create and compute path
    local path = game:GetService("PathfindingService"):CreatePath({
        AgentRadius = 2,
        AgentHeight = 5,
        AgentCanJump = true
    })

    local success = pcall(function()
        path:ComputeAsync(npc.model.PrimaryPart.Position, Vector3.new(coordinates.x, coordinates.y, coordinates.z))
    end)

    if success and path.Status == Enum.PathStatus.Success then
        local waypoints = path:GetWaypoints()
        for _, waypoint in ipairs(waypoints) do
            humanoid:MoveTo(waypoint.Position)
            humanoid.MoveToFinished:Wait()
        end
        return true
    end
    
    LoggerService:warn("NAVIGATION", "Path computation failed")
    return false
end

function NavigationService:Navigate(npc, destination, coordinates)
    if coordinates then
        LoggerService:debug("NAVIGATION", string.format(
            "Using direct coordinates for %s: %d, %d, %d",
            npc.displayName,
            coordinates.x,
            coordinates.y,
            coordinates.z
        ))
        return self:NavigateToCoordinates(npc, coordinates)
    end
    
    -- Fallback to existing destination logic
    return self:goToDestination(npc, destination)
end

return NavigationService 