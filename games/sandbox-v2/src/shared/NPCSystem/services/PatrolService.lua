local LoggerService = require(script.Parent.Parent.services.LoggerService)
local LocationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LocationService)
local NavigationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.NavigationService)

local PatrolService = {}
PatrolService.__index = PatrolService

local activePatrols = {}

function PatrolService.new()
    return setmetatable({}, PatrolService)
end

function PatrolService:getPatrolRoute(npc, options)
    if not npc or not npc.model then
        LoggerService:warn("PATROL", "Invalid NPC for patrol route generation")
        return nil
    end

    local patrolType = options and options.type or "full"
    LoggerService:debug("PATROL", string.format(
        "Generating %s patrol route for NPC %s",
        patrolType,
        npc.displayName
    ))

    -- Get all available locations
    local locations = LocationService:getAllLocations()
    if not locations or #locations == 0 then
        LoggerService:warn("PATROL", "No locations available for patrol")
        return nil
    end

    -- For full patrol, return all locations in a randomized order
    if patrolType == "full" then
        local route = {}
        -- Copy locations to avoid modifying original
        for _, loc in ipairs(locations) do
            table.insert(route, {
                name = loc.name,
                slug = loc.slug,
                position = loc.position
            })
        end
        
        -- Randomize order
        for i = #route, 2, -1 do
            local j = math.random(i)
            route[i], route[j] = route[j], route[i]
        end

        LoggerService:debug("PATROL", string.format(
            "Generated full patrol route with %d locations for NPC %s",
            #route,
            npc.displayName
        ))
        
        return route
    end
    
    -- For focused patrol around a target
    if patrolType == "focused" and options.target then
        local targetLoc = LocationService:getLocation(options.target)
        if targetLoc then
            -- Get nearby locations
            local nearbyLocs = LocationService:getNearbyLocations(targetLoc.position, 100)
            if nearbyLocs and #nearbyLocs > 0 then
                return nearbyLocs
            end
        end
    end

    LoggerService:warn("PATROL", string.format(
        "Could not generate patrol route for type: %s",
        patrolType
    ))
    return nil
end

function PatrolService:startPatrol(npc, options)
    if not npc or not npc.id then
        LoggerService:warn("PATROL", "Invalid NPC for patrol")
        return false
    end

    -- Stop any existing patrol
    self:stopPatrol(npc)

    -- Get patrol route
    local patrolRoute = self:getPatrolRoute(npc, options)
    if not patrolRoute or #patrolRoute == 0 then
        LoggerService:warn("PATROL", string.format(
            "No valid patrol route for NPC %s",
            npc.displayName
        ))
        return false
    end

    -- Initialize patrol state
    local patrol = {
        npc = npc,
        route = patrolRoute,
        currentIndex = 1,
        active = true,
        lastMoveTime = 0,
        minDuration = 30 -- 30 seconds at each location
    }
    
    activePatrols[npc.id] = patrol

    -- Start patrol loop
    task.spawn(function()
        while patrol.active do
            local currentLocation = patrol.route[patrol.currentIndex]
            local currentTime = os.time()

            -- Only move if we've stayed long enough
            if currentTime - patrol.lastMoveTime >= patrol.minDuration then
                LoggerService:debug("PATROL", string.format(
                    "NPC %s moving to %s",
                    npc.displayName,
                    currentLocation.name
                ))

                local success = NavigationService:Navigate(npc, currentLocation.position)
                if success then
                    patrol.lastMoveTime = currentTime
                    patrol.currentIndex = (patrol.currentIndex % #patrol.route) + 1
                else
                    LoggerService:warn("PATROL", string.format(
                        "Navigation failed for NPC %s to %s",
                        npc.displayName,
                        currentLocation.name
                    ))
                end
            end

            task.wait(1)
        end
    end)

    return true
end

function PatrolService:stopPatrol(npc)
    if not npc or not npc.id then return end
    
    if activePatrols[npc.id] then
        activePatrols[npc.id].active = false
        activePatrols[npc.id] = nil
        
        LoggerService:debug("PATROL", string.format(
            "Stopped patrol for NPC %s",
            npc.displayName
        ))
    end
end

return PatrolService 