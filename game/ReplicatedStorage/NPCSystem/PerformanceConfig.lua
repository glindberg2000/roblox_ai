local PerformanceConfig = {
    -- Logging Settings
    Logging = {
        Enabled = true,
        MinLevel = 4, -- 1=DEBUG, 2=INFO, 3=WARN, 4=ERROR
        BatchSize = 10,
        FlushInterval = 1, -- seconds
    },

    -- NPC Settings
    NPC = {
        -- Movement
        MovementEnabled = true,
        UpdateInterval = 5, -- seconds
        MovementChance = 0.8, -- 80% chance to move
        MovementRadius = 10, -- studs
        
        -- Range Checking
        RangeCheckInterval = 5, -- seconds
        ProximityEnabled = true,
        
        -- Animations
        AnimationsEnabled = true,
        AnimationDebounce = 0.2, -- seconds
    },

    -- Thread Management
    Threading = {
        MaxThreads = 10,
        ThreadTimeout = 5, -- seconds
        EnableParallel = true
    }
}

return PerformanceConfig 