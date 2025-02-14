local NavigationService = {}
local PathfindingService = game:GetService("PathfindingService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)
local LocationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LocationService)

-- Combat navigation parameters
local COMBAT_PARAMS = {
    AgentRadius = 2.0,        -- Smaller radius for tighter paths
    AgentHeight = 5.0,
    AgentCanJump = true,      -- Allow jumping in combat
    WaypointSpacing = 4.0,    -- Closer waypoints for precise tracking
    RECALCULATE_THRESHOLD = 8, -- Distance before recalculating path
    UPDATE_INTERVAL = 0.5      -- More frequent updates for combat
}

function NavigationService:NavigateToPosition(npc, targetPosition)
    -- Validate inputs
    if not npc or not targetPosition then
        LoggerService:warn("NAVIGATION", "Missing required parameters for navigation")
        return false
    end

    if typeof(targetPosition) ~= "Vector3" then
        LoggerService:warn("NAVIGATION", string.format(
            "Invalid position type for %s: expected Vector3, got %s",
            npc.displayName,
            typeof(targetPosition)
        ))
        return false
    end

    -- Safe logging with number validation
    local logMessage = "Attempting to navigate %s to position: %.1f, %.1f, %.1f"
    local success, _ = pcall(function()
        LoggerService:debug("NAVIGATION", string.format(
            logMessage,
            npc.displayName or "Unknown NPC",
            targetPosition.X,
            targetPosition.Y,
            targetPosition.Z
        ))
    end)

    if not success then
        LoggerService:warn("NAVIGATION", string.format(
            "Navigation started for %s to position (log failed)",
            npc.displayName or "Unknown NPC"
        ))
    end

    local humanoid = npc.model and npc.model:FindFirstChild("Humanoid")
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

    local pathSuccess, pathError = pcall(function()
        path:ComputeAsync(npc.model.PrimaryPart.Position, targetPosition)
    end)

    if pathSuccess and path.Status == Enum.PathStatus.Success then
        local waypoints = path:GetWaypoints()
        for _, waypoint in ipairs(waypoints) do
            humanoid:MoveTo(waypoint.Position)
            humanoid.MoveToFinished:Wait()
        end
        return true
    end
    
    LoggerService:warn("NAVIGATION", string.format(
        "Path computation failed for %s: %s",
        npc.displayName,
        tostring(pathError)
    ))
    return false
end

function NavigationService:NavigateToLocation(npc, locationSlug)
    if not locationSlug then
        LoggerService:warn("NAVIGATION", "No location slug provided")
        return false
    end

    local location = LocationService:getLocationBySlug(locationSlug)
    if not location then
        LoggerService:warn("NAVIGATION", string.format("Unknown location: %s", locationSlug))
        return false
    end
    
    LoggerService:debug("NAVIGATION", string.format(
        "Navigating %s to location: %s",
        npc.displayName or "Unknown NPC",
        location.name
    ))
    
    return self:NavigateToPosition(npc, location.position)
end

function NavigationService:Navigate(npc, destination)
    if not npc or not destination then
        LoggerService:warn("NAVIGATION", "Missing required parameters for navigation")
        return false
    end

    -- If destination is a Vector3, use it directly
    if typeof(destination) == "Vector3" then
        return self:NavigateToPosition(npc, destination)
    end
    
    -- Otherwise treat it as a location slug
    return self:NavigateToLocation(npc, destination)
end

function NavigationService:CombatNavigate(npc, target, huntType)
    if not npc or not npc.model or not target then
        LoggerService:warn("NAVIGATION", "Missing required parameters for combat navigation")
        return false
    end
    
    -- Get target character/model based on type
    local targetChar
    if typeof(target) == "Instance" then
        -- Target is a Player
        targetChar = target.Character
    elseif typeof(target) == "table" and target.model then
        -- Target is an NPC
        targetChar = target.model
    else
        targetChar = target
    end
    
    if not targetChar or not targetChar:FindFirstChild("HumanoidRootPart") then
        LoggerService:warn("NAVIGATION", "Invalid target for combat navigation")
        return false
    end
    
    -- Configure behavior based on hunt type
    local params = COMBAT_PARAMS
    if huntType == "destroy" then
        params = {
            AgentRadius = 2.0,
            AgentHeight = 5.0,
            AgentCanJump = true,
            WaypointSpacing = 2.0,  -- Closer spacing for aggressive pursuit
            RECALCULATE_THRESHOLD = 4, -- More frequent recalculation
            UPDATE_INTERVAL = 0.25  -- Faster updates
        }
    end
    
    -- Start combat navigation loop
    task.spawn(function()
        while npc.Active do
            local rootPart = npc.model:FindFirstChild("HumanoidRootPart")
            local humanoid = npc.model:FindFirstChild("Humanoid")
            if not rootPart or not humanoid then break end
            
            local targetPos = targetChar.HumanoidRootPart.Position
            local distance = (rootPart.Position - targetPos).Magnitude
            
            -- Navigate to target
            if distance > 5 then
                humanoid:MoveTo(targetPos)
            end
            
            task.wait(params.UPDATE_INTERVAL)
        end
    end)
    
    return true
end

return NavigationService 