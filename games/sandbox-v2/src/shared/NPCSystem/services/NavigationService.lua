local NavigationService = {}
NavigationService.__index = NavigationService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PathfindingService = game:GetService("PathfindingService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local LocationService = require(ReplicatedStorage.Shared.NPCSystem.services.LocationService)

-- Update the combat parameters to be more lenient
local NAVIGATION_PARAMS = {
    DEFAULT = {
        AgentRadius = 2.0,
        AgentHeight = 6.0,        -- Increased height
        AgentCanJump = true,
        AgentCanClimb = true,     -- Allow climbing
        WaypointSpacing = 8.0,    -- Increased spacing for faster movement
        Costs = {
            Water = 50,
            Grass = 5,
            Ground = 1
        }
    },
    FALLBACK = {
        AgentRadius = 1.5,        -- Slightly reduced for better pathing
        AgentHeight = 8.0,        -- Even higher height
        AgentCanJump = true,
        AgentCanClimb = true,
        WaypointSpacing = 12.0,   -- Even larger spacing
        Costs = {
            Water = 20,           -- More accepting of water
            Grass = 2,
            Ground = 1
        }
    }
}

function NavigationService:Navigate(npc, destination)
    if not npc or not npc.model then
        LoggerService:warn("NAVIGATION", "Invalid NPC or model for navigation")
        return false
    end

    local targetPosition
    if typeof(destination) == "Vector3" then
        targetPosition = destination
    elseif typeof(destination) == "CFrame" then
        targetPosition = destination.Position
    elseif type(destination) == "string" then
        -- Handle location slug lookup
        local locationPoint = self:getLocationPoint(destination)
        if not locationPoint then
            LoggerService:warn("NAVIGATION", string.format(
                "Could not find location point for %s",
                destination
            ))
            return false
        end
        targetPosition = locationPoint
    else
        LoggerService:warn("NAVIGATION", string.format(
            "Invalid destination type: %s",
            typeof(destination)
        ))
        return false
    end

    LoggerService:debug("NAVIGATION", string.format(
        "NavigateToPosition called for %s to position (%.1f, %.1f, %.1f)",
        npc.displayName,
        targetPosition.X,
        targetPosition.Y,
        targetPosition.Z
    ))

    -- Try navigation with default parameters first
    local success = self:TryNavigateWithParams(npc, targetPosition, NAVIGATION_PARAMS.DEFAULT)
    
    -- If default navigation fails, try with fallback parameters
    if not success then
        LoggerService:debug("NAVIGATION", string.format(
            "Retrying navigation for %s with fallback parameters",
            npc.displayName
        ))
        success = self:TryNavigateWithParams(npc, targetPosition, NAVIGATION_PARAMS.FALLBACK)
    end
    
    -- If both attempts fail, try direct movement as last resort
    if not success then
        LoggerService:debug("NAVIGATION", string.format(
            "Attempting direct movement for %s as fallback",
            npc.displayName
        ))
        return self:DirectMove(npc, targetPosition)
    end
    
    return success
end

function NavigationService:TryNavigateWithParams(npc, targetPosition, params)
    local path = PathfindingService:CreatePath(params)
    
    local success, errorMessage = pcall(function()
        path:ComputeAsync(npc.model.HumanoidRootPart.Position, targetPosition)
    end)
    
    if success and path.Status == Enum.PathStatus.Success then
        local waypoints = path:GetWaypoints()
        local currentWaypointIndex = 1
        
        -- Set initial movement speed
        npc.model.Humanoid.WalkSpeed = 20  -- Default to faster speed
        
        -- Connect to MoveToFinished event
        local moveConnection
        moveConnection = npc.model.Humanoid.MoveToFinished:Connect(function(reached)
            if reached and currentWaypointIndex < #waypoints then
                currentWaypointIndex += 1
                
                -- Move to next waypoint immediately
                if currentWaypointIndex <= #waypoints then
                    local nextWaypoint = waypoints[currentWaypointIndex]
                    
                    -- Handle jumping
                    if nextWaypoint.Action == Enum.PathWaypointAction.Jump then
                        npc.model.Humanoid.Jump = true
                    end
                    
                    npc.model.Humanoid:MoveTo(nextWaypoint.Position)
                else
                    moveConnection:Disconnect()
                end
            end
        end)
        
        -- Start initial movement
        if #waypoints > 0 then
            npc.model.Humanoid:MoveTo(waypoints[1].Position)
        end
        
        -- Monitor overall progress
        task.spawn(function()
            local startTime = tick()
            local timeout = math.max(20, #waypoints * 2) -- Scale timeout with path length
            
            repeat
                task.wait(0.1)
                if not npc.model or not npc.model:FindFirstChild("Humanoid") then
                    moveConnection:Disconnect()
                    return false
                end
                
                -- Check if we've reached the final destination
                if currentWaypointIndex == #waypoints and 
                   (npc.model.HumanoidRootPart.Position - targetPosition).Magnitude < 2 then
                    break
                end
            until tick() - startTime > timeout
            
            moveConnection:Disconnect()
        end)
        
        return true
    end
    
    return false
end

function NavigationService:DirectMove(npc, targetPosition)
    if not npc.model or not npc.model:FindFirstChild("Humanoid") then
        return false
    end
    
    LoggerService:debug("NAVIGATION", string.format(
        "Attempting direct movement for %s to position (%.1f, %.1f, %.1f)",
        npc.displayName,
        targetPosition.X,
        targetPosition.Y,
        targetPosition.Z
    ))
    
    -- Start direct movement
    task.spawn(function()
        npc.model.Humanoid:MoveTo(targetPosition)
        
        -- Wait for movement to complete or timeout
        local startTime = tick()
        local timeout = 10  -- 10 seconds timeout for direct movement
        
        repeat
            task.wait(0.1)
            if not npc.model or not npc.model:FindFirstChild("Humanoid") then
                return
            end
        until (npc.model.HumanoidRootPart.Position - targetPosition).Magnitude < 2
            or tick() - startTime > timeout
    end)
    
    return true
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
    
    return self:Navigate(npc, location.position)
end

function NavigationService:CombatNavigate(npc, target, huntType)
    if not npc or not target then
        LoggerService:warn("NAVIGATION", "Invalid NPC or target for combat navigation")
        return false
    end

    local targetChar = nil
    -- If target is an instance, check if it's a Player
    if typeof(target) == "Instance" then
        if target:IsA("Player") then
            if target.Character then
                targetChar = target.Character
                LoggerService:debug("NAVIGATION", "Target is Player " .. target.Name .. ", using Character: " .. tostring(targetChar))
            else
                LoggerService:warn("NAVIGATION", "Player target " .. target.Name .. " does not have a valid Character")
                return false
            end
        else
            -- For non-player instances, assume target is the model itself
            targetChar = target
            LoggerService:debug("NAVIGATION", "Target is non-player Instance, using target directly: " .. tostring(targetChar))
        end
    elseif typeof(target) == "table" and target.model then
        targetChar = target.model
        LoggerService:debug("NAVIGATION", "Target is table with model: " .. tostring(targetChar))
    else
        targetChar = target
        LoggerService:debug("NAVIGATION", "Target is direct: " .. tostring(targetChar))
    end

    -- Use HumanoidRootPart if present, otherwise fall back to PrimaryPart.
    local targetRoot = targetChar:FindFirstChild("HumanoidRootPart") or targetChar.PrimaryPart
    if not targetRoot then
        LoggerService:warn("NAVIGATION", string.format(
            "Invalid target for combat navigation:\nTarget: %s\nTargetRoot: %s",
            tostring(target),
            tostring(targetChar)
        ))
        return false
    end

    local npcRoot = npc.model:FindFirstChild("HumanoidRootPart") or npc.model.PrimaryPart
    if not npcRoot then
        LoggerService:warn("NAVIGATION", string.format(
            "NPC %s does not have a valid root part.",
            npc.displayName
        ))
        return false
    end

    -- Set up hunting state.
    npc.isHunting = true
    npc.huntTarget = targetChar
    npc.overrideMovement = true  -- Tell MovementService to skip this NPC

    -- Start the hunt loop.
    task.spawn(function()
        while npc.Active and npc.isHunting do
            local distance = (targetRoot.Position - npcRoot.Position).Magnitude

            -- If too far, navigate toward the target.
            if distance > 5 then
                local humanoid = npc.model:FindFirstChild("Humanoid")
                if humanoid then
                    humanoid:MoveTo(targetRoot.Position)
                end
            end

            task.wait(0.5) -- Update every half second.
        end

        -- Clean up after hunting.
        npc.isHunting = false
        npc.huntTarget = nil
        npc.overrideMovement = false
    end)

    return true
end

-- Helper function to get location points
function NavigationService:getLocationPoint(locationSlug)
    -- TODO: Implement proper location point lookup
    -- For now, return hardcoded points for testing
    local locationPoints = {
        ["petes_merch_stand"] = Vector3.new(-12, 18.9, -127),
        -- Add more location points as needed
    }
    
    return locationPoints[locationSlug]
end

return NavigationService 