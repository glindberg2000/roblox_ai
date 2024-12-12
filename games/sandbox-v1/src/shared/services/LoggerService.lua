-- LoggerService.lua
local LoggerService = {
    LOG_LEVELS = {
        DEBUG = 1,
        INFO = 2,
        WARN = 3,
        ERROR = 4
    },
    
    CATEGORIES = {
        SYSTEM = true,
        ANIMATION = true,
        INTERACTION = true,
        MOVEMENT = true,
        VISION = true,
        CHAT = true,
        DATABASE = true,
        THREAD = true,
        STATE = true,
        API = true,
        DEBUG = true
    }
}

local currentLogLevel = LoggerService.LOG_LEVELS.DEBUG
local enabledCategories = {}

-- Initialize all categories as enabled by default
for category, _ in pairs(LoggerService.CATEGORIES) do
    enabledCategories[category] = true
end

function LoggerService:setLogLevel(level)
    if self.LOG_LEVELS[level] then
        currentLogLevel = self.LOG_LEVELS[level]
    end
end

function LoggerService:enableCategory(category)
    enabledCategories[category] = true
end

function LoggerService:disableCategory(category)
    enabledCategories[category] = false
end

function LoggerService:log(category, message, level)
    level = level or self.LOG_LEVELS.INFO
    
    -- Check if category is enabled and message meets minimum log level
    if not enabledCategories[category] or level < currentLogLevel then
        return
    end
    
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    print(string.format("[%s] [%s] %s", timestamp, category, message))
end

return LoggerService 