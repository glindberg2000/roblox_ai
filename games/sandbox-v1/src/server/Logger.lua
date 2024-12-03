-- Logger.lua
local Logger = {}

-- Define log categories and their enabled state
local LOG_CATEGORIES = {
    SYSTEM = true,
    ERROR = true,
    WARN = true,
    DEBUG = true,
    CHAT = true,
    INTERACTION = true,
    STATE = true,
    DATABASE = true,
    NPC = true,
    ASSET = true,
    API = true,
    SPAWN = true,
    LOCK = true,
    UNLOCK = true,
    MOVEMENT = true,
    ACTION = true,
    RESPONSE = true,
    VISION = true,        -- Enable vision logging
    PERCEPTION = true,    -- Enable perception logging
    DISTANCE = true,      -- Enable distance calculations
    TRIGGER = true,       -- Enable interaction trigger logging
}

-- Define log levels and their colors
local LOG_COLORS = {
    SYSTEM = Color3.fromRGB(255, 255, 255),    -- White
    ERROR = Color3.fromRGB(255, 0, 0),         -- Red
    WARN = Color3.fromRGB(255, 165, 0),        -- Orange
    DEBUG = Color3.fromRGB(173, 216, 230),     -- Light blue
    VISION = Color3.fromRGB(144, 238, 144),    -- Light green
    PERCEPTION = Color3.fromRGB(147, 112, 219), -- Purple
    DISTANCE = Color3.fromRGB(255, 218, 185),  -- Peach
    TRIGGER = Color3.fromRGB(255, 192, 203),   -- Pink
    -- ... rest of colors
}

-- Current log level - can be changed at runtime
Logger.currentLevel = Logger.LogLevel.DEBUG

-- Category filters - Uncomment to disable specific categories
Logger.categoryFilters = {
    -- System & Debug
    -- SYSTEM = false,    -- System-level messages
    -- DEBUG = false,     -- Debug information
    -- ERROR = false,     -- Error messages
    
    -- NPC Behavior
    -- VISION = false,    -- NPC vision updates
    -- MOVEMENT = false,  -- NPC movement
    -- ACTION = false,    -- NPC actions
    -- ANIMATION = false, -- NPC animations
    
    -- Interaction & Chat
    -- CHAT = false,      -- Chat messages
    -- INTERACTION = false, -- Player-NPC interactions
    -- RESPONSE = false,  -- AI responses
    
    -- State & Data
    -- STATE = false,     -- State changes
    -- DATABASE = false,  -- Database operations
    -- ASSET = false,     -- Asset loading/management
    -- API = false,       -- API calls
}

function Logger:setLogLevel(level)
    if self.LogLevel[level] then
        self.currentLevel = self.LogLevel[level]
    end
end

function Logger:enableCategory(category)
    self.categoryFilters[category] = true
    print(string.format("Enabled logging for category: %s", category))
end

function Logger:disableCategory(category)
    self.categoryFilters[category] = false
    print(string.format("Disabled logging for category: %s", category))
end

function Logger:log(category, message, ...)
    -- Check if category is explicitly disabled
    if self.categoryFilters[category] == false then
        return
    end
    
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    
    -- Handle old-style logging (single message parameter)
    if message == nil then
        -- If only one parameter was passed, treat it as the message
        print(string.format("[%s] %s", timestamp, category))
        return
    end
    
    -- Handle new-style logging (category + message)
    print(string.format("[%s] [%s] %s", timestamp, category:upper(), message))
end

-- Convenience methods for each category
function Logger:vision(message)
    self:log("VISION", message)
end

function Logger:movement(message)
    self:log("MOVEMENT", message)
end

function Logger:interaction(message)
    self:log("INTERACTION", message)
end

function Logger:database(message)
    self:log("DATABASE", message)
end

function Logger:asset(message)
    self:log("ASSET", message)
end

function Logger:api(message)
    self:log("API", message)
end

function Logger:state(message)
    self:log("STATE", message)
end

function Logger:animation(message)
    self:log("ANIMATION", message)
end

function Logger:error(message)
    self:log("ERROR", message)
end

function Logger:debug(message)
    self:log("DEBUG", message)
end

-- Example usage:
-- To disable vision logs, uncomment this line:
-- Logger.categoryFilters.VISION = false
-- Logger.categoryFilters.MOVEMENT = false
-- Logger.categoryFilters.ANIMATION = false
-- To re-enable vision logs, uncomment this line:
-- Logger.categoryFilters.VISION = true

-- You can also use these functions in your code:
-- Logger:disableCategory("VISION")
-- Logger:enableCategory("VISION")

-- Enable categories we want to debug
Logger.categoryFilters.VISION = true
Logger.categoryFilters.PERCEPTION = true
Logger.categoryFilters.DISTANCE = true
Logger.categoryFilters.TRIGGER = true
Logger.categoryFilters.MOVEMENT = true
Logger.categoryFilters.INTERACTION = true

return Logger