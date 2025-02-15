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
    LoggerService:debug("NAVIGATION", string.format(
        "NavigateToPosition called for %s to position (%.1f, %.1f, %.1f)",
        npc.displayName,
        targetPosition.X,
        targetPosition.Y,
        targetPosition.Z
    ))

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
    if not npc or not target then
        LoggerService:warn("NAVIGATION", "Invalid NPC or target for combat navigation")
        return false
    end

    -- Debug log the target type and properties
    LoggerService:debug("NAVIGATION", string.format(
        "Target details:\nType: %s\nProperties: %s",
        typeof(target),
        table.concat({
            "Name=" .. (target.Name or "nil"),
            "DisplayName=" .. (target.displayName or "nil"),
            "Model=" .. (target.model and "exists" or "nil"),
            "Character=" .. (target.Character and "exists" or "nil")
        }, ", ")
    ))

    -- Get target character/model based on type
    local targetChar
    if typeof(target) == "Instance" then
        targetChar = target.Character
        LoggerService:debug("NAVIGATION", "Target is Instance, Character: " .. tostring(targetChar))
    elseif typeof(target) == "table" and target.model then
        targetChar = target.model
        LoggerService:debug("NAVIGATION", "Target is table with model: " .. tostring(targetChar))
    else
        targetChar = target
        LoggerService:debug("NAVIGATION", "Target is direct: " .. tostring(targetChar))
    end

    -- Validate target has required parts
    if not targetChar or not targetChar:FindFirstChild("HumanoidRootPart") then
        LoggerService:warn("NAVIGATION", string.format(
            "Invalid target for combat navigation:\nTarget: %s\nCharacter: %s\nHas HumanoidRootPart: %s",
            tostring(target),
            tostring(targetChar),
            tostring(targetChar and targetChar:FindFirstChild("HumanoidRootPart"))
        ))
        return false
    end

    -- Set hunting state
    npc.isHunting = true
    npc.huntTarget = targetChar
    npc.overrideMovement = true  -- Tell MovementService to skip this NPC

    -- Start hunt loop
    task.spawn(function()
        while npc.Active and npc.isHunting do
            local targetPos = targetChar.HumanoidRootPart.Position
            local npcPos = npc.model.HumanoidRootPart.Position
            local distance = (targetPos - npcPos).Magnitude

            -- If we're too far, navigate to target
            if distance > 5 then
                local humanoid = npc.model:FindFirstChild("Humanoid")
                if humanoid then
                    humanoid:MoveTo(targetPos)
                end
            end

            task.wait(0.5) -- Update every half second
        end

        -- Clean up hunting state
        npc.isHunting = false
        npc.huntTarget = nil
        npc.overrideMovement = false  -- Restore MovementService control
    end)

    return true
end

return NavigationService 