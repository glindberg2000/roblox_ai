print("LoggerService loaded")

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR"
export type LogCategory = "SYSTEM" | "NPC" | "CHAT" | "INTERACTION" | "MOVEMENT" | "ANIMATION" | "DATABASE" | "API" | "SNAPSHOT" | "RANGE"

local SHOW_CLUSTER_LOGS = false -- Set to true to see cluster debug logs

local LoggerService = {
    isDebugEnabled = true,
    
    -- Define categories and their log levels
    categories = {
        SNAPSHOT = {
            enabled = true,
            minLevel = "DEBUG"
        },
        SYSTEM = {
            enabled = true,
            minLevel = "INFO"
        },
        RANGE = {
            enabled = true,
            minLevel = "WARN"
        },
        ANIMATION = {
            enabled = true,
            minLevel = "WARN"
        },
        MODEL = {
            enabled = true,
            minLevel = "INFO"
        },
        PROXIMITY_MATRIX = {
            enabled = true,
            minLevel = "WARN"
        },
        NPC = {
            enabled = true,
            minLevel = "INFO"
        },
        CHAT = {
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
    
    config = {
        timeFormat = "%Y-%m-%d %H:%M:%S",
        outputToFile = false,
        outputPath = "logs/"
    }
}

local LOG_LEVELS = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4
}

function LoggerService:shouldLog(category: LogCategory, level: LogLevel): boolean
    -- Always allow if no category config exists
    if not self.categories[category] then
        return true
    end
    
    local categoryConfig = self.categories[category]
    if not categoryConfig.enabled then return false end
    
    return LOG_LEVELS[level] >= LOG_LEVELS[categoryConfig.minLevel]
end

function LoggerService:formatMessage(level: LogLevel, category: LogCategory, message: string): string
    local timestamp = os.date(self.config.timeFormat)
    return string.format("[%s] [%s] [%s] %s", timestamp, level, category, tostring(message))
end

function LoggerService:log(level: LogLevel, category: LogCategory, message: string)
    if not self:shouldLog(category, level) then return end
    
    local formattedMessage = self:formatMessage(level, category, message)
    print(formattedMessage)
    
    if self.config.outputToFile then
        -- TODO: Implement file output
    end
end

function LoggerService:debug(category: LogCategory, message: string)
    if not SHOW_CLUSTER_LOGS and category == "CLUSTER" then
        return
    end
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

function LoggerService:setMinLevel(category: LogCategory, level: LogLevel)
    if self.categories[category] then
        self.categories[category].minLevel = level
    end
end

function LoggerService:enableCategory(category: LogCategory)
    if self.categories[category] then
        self.categories[category].enabled = true
    end
end

function LoggerService:disableCategory(category: LogCategory)
    if self.categories[category] then
        self.categories[category].enabled = false
    end
end

return LoggerService 