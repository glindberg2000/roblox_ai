print("LoggerService loaded")

local LoggerService = {}

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR"
export type LogCategory = "SYSTEM" | "NPC" | "CHAT" | "INTERACTION" | "MOVEMENT" | "ANIMATION" | "DATABASE" | "API" | "SNAPSHOT"

local config = {
    enabled = true,
    minLevel = "INFO",
    enabledCategories = {
        SYSTEM = {
            debug = true,
            info = true,
            warn = true,
            error = true
        },
        NPC = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        CHAT = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        INTERACTION = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        MOVEMENT = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        ANIMATION = false,
        DATABASE = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        API = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        PROXIMITY_MATRIX = {
            debug = false,
            info = false,
            warn = true,
            error = true
        },
        SNAPSHOT = {
            debug = true,
            info = true,
            warn = true,
            error = true
        }
    },
    timeFormat = "%Y-%m-%d %H:%M:%S",
    outputToFile = false,
    outputPath = "logs/"
}

local levelPriority = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4
}

function LoggerService:shouldLog(level: LogLevel, category: LogCategory): boolean
    if not config.enabled then return false end
    
    if type(config.enabledCategories[category]) == "table" then
        return config.enabledCategories[category][string.lower(level)] or false
    end
    
    if not config.enabledCategories[category] then return false end
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
function LoggerService:setMinLevel(level: LogLevel)
    config.minLevel = level
end

function LoggerService:enableCategory(category: LogCategory)
    config.enabledCategories[category] = true
end

function LoggerService:disableCategory(category: LogCategory)
    config.enabledCategories[category] = false
end

return LoggerService 