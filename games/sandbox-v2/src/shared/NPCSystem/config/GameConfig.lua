--[[
    GameConfig.lua
    Central configuration file for the NPC system
]]

local GameConfig = {
    -- State Management & Snapshots
    StateSync = {
        UPDATE_INTERVAL = 2,      -- Local state updates (seconds)
        API_SYNC_INTERVAL = 10,   -- Backend sync interval (seconds)
        CACHE_EXPIRY = 30,        -- Cache expiry (seconds)
        MOVEMENT_THRESHOLD = 0.1   -- Min movement to record (studs)
    },

    -- API Configuration (imported from LettaConfig)
    API = require(script.Parent.LettaConfig),

    -- Legacy configs maintained for compatibility
    UseNewActionSystem = false,   -- From config.lua
}

return GameConfig 