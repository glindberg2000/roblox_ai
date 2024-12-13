local PerformanceConfig = {
    -- Logging Settings
    Logging = {
        Enabled = true,
        MinLevel = 4, -- 1=DEBUG, 2=INFO, 3=WARN, 4=ERROR
        BatchSize = 10,
        FlushInterval = 1, -- seconds
        DetailedAssets = false, -- Detailed asset logging
        AnimationErrors = false, -- Log animation state errors
        BatchProcessing = true,  -- Enable log batching
        DebugNPCStates = false  -- Detailed NPC state logging
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
        ProximityRadius = 4, -- studs
        
        -- Vision & Raycasting
        VisionEnabled = false,
        VisionUpdateRate = 0.5, -- seconds between vision updates
        MaxVisionDistance = 50, -- max raycast distance
        RaycastBatchSize = 5,  -- number of raycasts per frame
        SkipOccludedTargets = true, -- skip targets behind walls
        VisionConeAngle = 120, -- vision cone in degrees
        
        -- Animations
        AnimationsEnabled = true,
        AnimationDebounce = 0.2, -- seconds
        
        -- Performance Tuning
        MaxActiveNPCs = 10,    -- Maximum NPCs active at once
        CullDistance = 100,    -- Distance at which to disable NPCs
        LODDistance = 50      -- Distance for lower detail
    },

    -- Thread Management
    Threading = {
        MaxThreads = 10,
        ThreadTimeout = 5, -- seconds
        EnableParallel = true,
        ThreadPoolSize = 5
    },

    -- Chat Settings
    Chat = {
        Enabled = true,
        CooldownTime = 1, -- seconds between messages
        MaxMessagesPerMinute = 30,
        BatchProcessing = true,
        BatchSize = 5,
        LogAllMessages = true, -- Log all chat messages
        DetailedLogging = true -- Log detailed chat info
    },

    -- Performance Monitoring
    Monitoring = {
        Enabled = true,
        LogInterval = 60, -- Log metrics every 60 seconds
        AlertThresholds = {
            minFPS = 30,
            maxMemoryMB = 1000,
            maxNetworkKbps = 1000
        }
    }
}

return PerformanceConfig 