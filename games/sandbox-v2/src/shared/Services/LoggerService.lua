local LoggerService = {}

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR"
export type LogCategory = 
    "SYSTEM" | "NPC" | "CHAT" | "INTERACTION" | 
    "MOVEMENT" | "ANIMATION" | "DATABASE" | "API" |
    "CONTEXT" | "PROXIMITY"

-- Enhanced configuration with subcategories
local config = {
    enabled = true,
    minLevel = "INFO",
    
    -- Detailed category configuration
    categories = {
        ANIMATION = {
            enabled = false,  -- Disable animation logs completely
            minLevel = "ERROR" -- Only show animation errors
        },
        MOVEMENT = {
            enabled = true,
            minLevel = "INFO"
        },
        PROXIMITY = {
            enabled = true,
            minLevel = "INFO"
        },
        CONTEXT = {
            enabled = true,
            minLevel = "INFO"
        },
        SYSTEM = {
            enabled = true,
            minLevel = "INFO"
        },
        CHAT = {
            enabled = true,
            minLevel = "INFO"
        },
        INTERACTION = {
            enabled = true,
            minLevel = "INFO"
        },
        DATABASE = {
            enabled = true,
            minLevel = "INFO"
        },
        API = {
            enabled = true,
            minLevel = "INFO"
        }
    },
    
    timeFormat = "%Y-%m-%d %H:%M:%S",
    outputToFile = false
}

local levelPriority = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4
}

function LoggerService:shouldLog(level: LogLevel, category: LogCategory): boolean
    if not config.enabled then return false end
    
    -- Check category-specific settings
    local categoryConfig = config.categories[category]
    if categoryConfig then
        if not categoryConfig.enabled then return false end
        if levelPriority[level] < levelPriority[categoryConfig.minLevel] then
            return false
        end
    end
    
    return levelPriority[level] >= levelPriority[config.minLevel]
end

function LoggerService:formatMessage(level: LogLevel, category: LogCategory, message: string): string
    local timestamp = os.date(config.timeFormat)
    return string.format("[%s] [%s] [%s] %s", timestamp, level, category, message)
end

function LoggerService:log(level: LogLevel, category: LogCategory, message: string)
    if not self:shouldLog(level, category) then return end
    
    local formattedMessage = self:formatMessage(level, category, message)
    print(formattedMessage)
    
    if config.outputToFile then
        -- TODO: Implement file output
    end
end

-- Convenience methods
function LoggerService:debug(category: LogCategory, message: string)
    self:log("DEBUG", category, message)
end

function LoggerService:info(category: LogCategory, message: string)
    self:log("INFO", category, message)
end

function LoggerService:warn(category: LogCategory, message: string)
    self:log("WARN", category, message)
end

function LoggerService:error(category: LogCategory, message: string)
    self:log("ERROR", category, message)
end

-- Configuration methods
function LoggerService:setCategoryLevel(category: LogCategory, level: LogLevel)
    if config.categories[category] then
        config.categories[category].minLevel = level
    end
end

function LoggerService:enableCategory(category: LogCategory)
    if config.categories[category] then
        config.categories[category].enabled = true
    end
end

function LoggerService:disableCategory(category: LogCategory)
    if config.categories[category] then
        config.categories[category].enabled = false
    end
end

function LoggerService:configureCategory(category: LogCategory, enabled: boolean, minLevel: LogLevel)
    if config.categories[category] then
        config.categories[category].enabled = enabled
        config.categories[category].minLevel = minLevel
    end
end

return LoggerService 