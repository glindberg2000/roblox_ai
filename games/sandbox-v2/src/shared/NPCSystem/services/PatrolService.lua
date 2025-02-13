local PatrolService = {}
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)
local LocationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LocationService)
local NavigationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.NavigationService)

-- Track active patrols
local activePatrols = {}

function PatrolService:startPatrol(npc, options)
    if not npc or not npc.id then
        LoggerService:warn("PATROL", "Invalid NPC provided for patrol")
        return false
    end

    -- Stop any existing patrol
    if activePatrols[npc.id] then
        self:stopPatrol(npc)
    end

    -- Get patrol route
    local patrolRoute = self:getPatrolRoute(npc, options)
    if not patrolRoute or #patrolRoute == 0 then
        LoggerService:warn("PATROL", string.format(
            "Could not generate patrol route for NPC %s",
            npc.displayName
        ))
        return false
    end

    -- Start patrol coroutine
    local patrol = {
        npc = npc,
        route = patrolRoute,
        currentIndex = 1,
        active = true
    }
    
    activePatrols[npc.id] = patrol
    
    task.spawn(function()
        while patrol.active do
            local currentLocation = patrol.route[patrol.currentIndex]
            
            LoggerService:debug("PATROL", string.format(
                "NPC %s patrolling to %s",
                npc.displayName,
                currentLocation.name
            ))
            
            -- Get coordinates from LocationService
            local coordinates = LocationService:getCoordinates(currentLocation.slug)
            if not coordinates then
                LoggerService:warn("PATROL", string.format(
                    "Could not get coordinates for location %s",
                    currentLocation.name
                ))
                task.wait(5)
                continue
            end
            
            local success = NavigationService:Navigate(npc, coordinates)
            
            if success then
                -- Move to next location
                patrol.currentIndex = patrol.currentIndex % #patrol.route + 1
                task.wait(2) -- Wait between locations
            else
                LoggerService:warn("PATROL", string.format(
                    "Navigation failed for NPC %s during patrol",
                    npc.displayName
                ))
                task.wait(5) -- Wait longer on failure
            end
        end
    end)
    
    return true
end

function PatrolService:stopPatrol(npc)
    if not npc or not npc.id then return end
    
    local patrol = activePatrols[npc.id]
    if patrol then
        patrol.active = false
        activePatrols[npc.id] = nil
        
        LoggerService:debug("PATROL", string.format(
            "Stopped patrol for NPC %s",
            npc.displayName
        ))
    end
end

function PatrolService:getPatrolRoute(npc, options)
    -- Get current position
    local currentPosition = npc.model and npc.model.PrimaryPart and npc.model.PrimaryPart.Position
    if not currentPosition then return nil end
    
    -- Handle different patrol types
    local patrolType = options and options.type or "full" -- "full" or "focused"
    local target = options and options.target
    
    if patrolType == "focused" and target then
        -- Get target and nearby locations to create a patrol route
        local targetLocation = LocationService:getLocation(target)
        if targetLocation then
            local route = {targetLocation}
            
            -- Get 2-3 nearby locations to patrol between
            local nearbyLocations = LocationService:getNearbyLocations(targetLocation.coordinates, 50)
            local usedSlugs = {[targetLocation.slug] = true}
            
            -- Add some variety to the patrol route
            for _, location in ipairs(nearbyLocations) do
                if not usedSlugs[location.slug] then
                    table.insert(route, location)
                    usedSlugs[location.slug] = true
                    if #route >= 3 then break end
                end
            end
            
            -- Add target location again to complete the loop
            table.insert(route, targetLocation)
            return route
        end
    end
    
    -- Full map patrol
    if patrolType == "full" then
        -- Get all available locations
        local allLocations = LocationService:getAllLocations()
        local route = {}
        
        -- Start from current location
        local startLocation = LocationService:getNearestLocation(currentPosition)
        if startLocation then
            table.insert(route, startLocation)
        end
        
        -- Add 4-6 major locations for a full patrol
        local locationCount = math.random(4, 6)
        local usedSlugs = {[startLocation.slug] = true}
        
        for _ = 1, locationCount do
            local randomLocation = allLocations[math.random(#allLocations)]
            if not usedSlugs[randomLocation.slug] then
                table.insert(route, randomLocation)
                usedSlugs[randomLocation.slug] = true
            end
        end
        
        -- Complete the loop
        if startLocation then
            table.insert(route, startLocation)
        end
        
        return route
    end
    
    return nil
end

return PatrolService 