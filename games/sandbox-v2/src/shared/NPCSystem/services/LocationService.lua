local LocationService = {}

-- Constants
local LOCATION_RADIUS = 20 -- Distance to consider "at" a location

-- State
local knownLocations = {
    {
        name = "Pete's Merch Stand",
        slug = "petes_merch_stand",
        position = Vector3.new(-12.0, 18.9, -127.0)
    },
    {
        name = "The Crematorium",
        slug = "the_crematorium",
        position = Vector3.new(-44.0, 21.0, -167.7)
    },
    {
        name = "Calvin's Calzone Restaurant",
        slug = "calvins_calzone_restaurant",
        position = Vector3.new(-21.9, 21.5, -103.0)
    },
    {
        name = "Chipotle",
        slug = "chipotle",
        position = Vector3.new(-19.0, 21.3, -8.2)
    },
    {
        name = "The Barber Boys",
        slug = "the_barber_boys",
        position = Vector3.new(-80.0, 21.3, -11.2)
    },
    {
        name = "Grocery Spelunking",
        slug = "grocery_spelunking",
        position = Vector3.new(-193.619, 27.775, 6.667)
    },
    {
        name = "Egg Cafe",
        slug = "egg_cafe",
        position = Vector3.new(-235.452, 26.0, -80.319)
    },
    {
        name = "Bluesteel Hotel",
        slug = "bluesteel_hotel",
        position = Vector3.new(-242.612, 32.15, -4.157)
    },
    {
        name = "Yellow House",
        slug = "yellow_house",
        position = Vector3.new(71.474, 26.65, -138.574)
    },
    {
        name = "Red House",
        slug = "red_house",
        position = Vector3.new(69.75, 24.42, -93.0)
    },
    {
        name = "Blue House",
        slug = "blue_house",
        position = Vector3.new(70.68, 26.65, -43.41)
    },
    {
        name = "Green House",
        slug = "green_house",
        position = Vector3.new(69.76, 24.89, 15.33)
    },
    {
        name = "DVDs",
        slug = "dvds",
        position = Vector3.new(-221.83, 26.0, -112.0)
    }
}

local lastKnownLocations = {}

-- Get nearest location to a position
function LocationService:getNearestLocation(position)
    local nearest = nil
    local nearestDistance = math.huge
    
    for _, loc in ipairs(knownLocations) do
        local distance = (position - loc.position).Magnitude
        if distance < nearestDistance then
            nearestDistance = distance
            nearest = {
                name = loc.name,
                slug = loc.slug,
                distance = math.floor(distance * 10) / 10
            }
        end
    end
    
    return nearest, nearestDistance <= LOCATION_RADIUS
end

-- Update NPC's last known location
function LocationService:updateNPCLocation(npcId, position)
    local nearest, isNear = self:getNearestLocation(position)
    local lastLocation = lastKnownLocations[npcId]
    
    if isNear then
        if lastLocation ~= nearest.slug then
            lastKnownLocations[npcId] = nearest.slug
            return true, nearest, lastLocation
        end
    elseif lastLocation then
        lastKnownLocations[npcId] = nil
        return true, nearest, lastLocation
    end
    
    return false, nearest, lastLocation
end

-- Get location position by name
function LocationService:getLocationBySlug(slug)
    for _, loc in ipairs(knownLocations) do
        if loc.slug == slug then
            return loc
        end
    end
    return nil
end

-- Get all known locations
function LocationService:getAllLocations()
    return knownLocations
end

-- Get NPC's last known location
function LocationService:getNPCLastLocation(npcId)
    return lastKnownLocations[npcId]
end

function LocationService:getCoordinates(slug)
    local location = self:getLocationBySlug(slug)
    if not location then
        return nil
    end
    
    -- Return the position Vector3 directly
    return location.position
end

return LocationService 