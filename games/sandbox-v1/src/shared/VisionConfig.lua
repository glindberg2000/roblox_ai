return {
    VISION_RANGE = 30, -- Studs
    
    -- Categories of objects NPCs can "see"
    VISIBLE_TAGS = {
        LANDMARK = "landmark",  -- Buildings, stations
        VEHICLE = "vehicle",    -- Cars, trains
        ITEM = "item",         -- Interactive items
        EVENT = "event"        -- Temporary events/activities
    },
    
    -- Cache descriptions for common objects
    ASSET_DESCRIPTIONS = {
        ["TrainStation"] = "A bustling train station with multiple platforms",
        ["Tesla_Cybertruck"] = "A futuristic angular electric vehicle",
        ["HawaiiStore"] = "A colorful shop selling beach gear and souvenirs",
        -- Add more asset descriptions...
    }
} 