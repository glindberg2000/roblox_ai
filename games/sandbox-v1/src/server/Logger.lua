-- Logger.lua
local Logger = {}

-- Define log levels
Logger.LogLevel = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4,
    NONE = 5
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
Logger.categoryFilters.VISION = false
Logger.categoryFilters.MOVEMENT = false
Logger.categoryFilters.ANIMATION = false
-- To re-enable vision logs, uncomment this line:
-- Logger.categoryFilters.VISION = true

-- You can also use these functions in your code:
-- Logger:disableCategory("VISION")
-- Logger:enableCategory("VISION")

return Logger