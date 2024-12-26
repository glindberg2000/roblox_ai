local NavigationService = {}
local PathfindingService = game:GetService("PathfindingService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)
local AnimationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.AnimationService)

-- Predefined destinations (can be moved to a config file later)
local Destinations = {
    town_center = Vector3.new(100, 10, 200),
    blacksmith = Vector3.new(-50, 10, 300),
    castle = Vector3.new(200, 10, -100),
    ["petes_merch_stand"] = Vector3.new(-10.289, 21.512, -127.797),
    ["petes_stand"] = Vector3.new(-10.289, 21.512, -127.797),
    ["merch_stand"] = Vector3.new(-10.289, 21.512, -127.797),
    ["stand"] = Vector3.new(-10.289, 21.512, -127.797),
    ["merch"] = Vector3.new(-10.289, 21.512, -127.797)
}

-- Add simple aliases/normalization
local function normalizeDestination(destinationName)
    -- Convert to lowercase
    local name = string.lower(destinationName)
    
    -- Simple mapping for common variations
    local aliases = {
        ["the stand"] = "petes_merch_stand",
        ["stand"] = "petes_merch_stand",
        ["merchant stand"] = "petes_merch_stand",
        ["petes stand"] = "petes_merch_stand",
        ["pete stand"] = "petes_merch_stand",
        ["petes_stand"] = "petes_merch_stand"
    }
    
    return aliases[name] or destinationName
end

function NavigationService:goToDestination(npc, destinationName)
    -- Ensure movement is unlocked here too
    npc.movementLocked = false
    
    -- Check if movement is locked
    if npc.isMovementLocked then
        LoggerService:warn("NAVIGATION", string.format(
            "NPC %s movement is locked - cannot navigate",
            npc.displayName
        ))
        return false
    end

    -- Check humanoid state
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        LoggerService:debug("NAVIGATION", string.format(
            "Humanoid state - WalkSpeed: %0.1f, MoveDirection: %s",
            humanoid.WalkSpeed,
            tostring(humanoid.MoveDirection)
        ))
    end

    -- Before navigation starts
    if humanoid then
        -- Store original walk speed
        local originalWalkSpeed = humanoid.WalkSpeed
        
        -- Set walk speed for navigation
        humanoid.WalkSpeed = 16  -- or whatever speed is appropriate
        
        -- After navigation completes
        humanoid.WalkSpeed = originalWalkSpeed
    end

    -- Normalize the destination name first
    local normalizedName = normalizeDestination(destinationName)
    local destination = Destinations[normalizedName]
    
    if not destination then
        LoggerService:warn("NAVIGATION", string.format(
            "Unknown destination: %s (normalized from: %s)", 
            normalizedName, 
            destinationName
        ))
        return false
    end

    -- Add distance logging
    local currentPos = npc.model.PrimaryPart.Position
    local distance = (destination - currentPos).Magnitude
    LoggerService:debug("NAVIGATION", string.format(
        "NPC %s navigating to %s - Distance: %0.1f studs",
        npc.displayName,
        normalizedName,
        distance
    ))

    LoggerService:debug("NAVIGATION", string.format(
        "NPC %s navigating to %s at position (%0.1f, %0.1f, %0.1f)",
        npc.displayName,
        normalizedName,
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

    -- Get waypoints first
    local waypoints = path:GetWaypoints()

    -- Then log the success with waypoint count
    LoggerService:debug("NAVIGATION", string.format(
        "Path computed successfully for %s with %d waypoints",
        npc.displayName,
        #waypoints
    ))

    -- Follow path
    for i, waypoint in ipairs(waypoints) do
        LoggerService:debug("NAVIGATION", string.format(
            "Moving to waypoint %d/%d - Current Position: (%0.1f, %0.1f, %0.1f), Target: (%0.1f, %0.1f, %0.1f)",
            i,
            #waypoints,
            npc.model.PrimaryPart.Position.X,
            npc.model.PrimaryPart.Position.Y,
            npc.model.PrimaryPart.Position.Z,
            waypoint.Position.X,
            waypoint.Position.Y,
            waypoint.Position.Z
        ))

        npc.model.Humanoid:MoveTo(waypoint.Position)
        
        -- Monitor movement
        local startTime = tick()
        local moveComplete = false
        
        npc.model.Humanoid.MoveToFinished:Connect(function()
            moveComplete = true
        end)
        
        -- Wait with timeout
        while not moveComplete and (tick() - startTime) < 5 do
            task.wait(0.1)
            LoggerService:debug("NAVIGATION", string.format(
                "Moving... Distance to waypoint: %0.1f studs",
                (npc.model.PrimaryPart.Position - waypoint.Position).Magnitude
            ))
        end
        
        if not moveComplete then
            LoggerService:warn("NAVIGATION", "Movement timed out - trying next waypoint")
        end
    end

    LoggerService:debug("NAVIGATION", string.format(
        "NPC %s reached destination %s",
        npc.displayName,
        normalizedName
    ))
    return true
end

return NavigationService 