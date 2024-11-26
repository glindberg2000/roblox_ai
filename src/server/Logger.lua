local Logger = {}
Logger.logs = {}
Logger.maxBufferSize = 100
Logger.logTypes = {
    general = true,  -- Enable general logs by default
    error = true,    -- Enable error logs by default
}

-- Constants for log types
Logger.LOG_TYPES = {
    GENERAL = "general",
    ERROR = "error",
    VISION = "vision",
    CONVERSATION = "conversation",
    ACTION = "action",
    MOVEMENT = "movement",
    INTERACTION = "interaction",
    DEBUG = "debug",
    SYSTEM = "system",
}

-- Enable specific log types
function Logger:enableLogType(logType)
    self.logTypes[logType] = true
    self:log("Enabled logging for: " .. logType, "system")
end

-- Disable specific log types
function Logger:disableLogType(logType)
    self.logTypes[logType] = nil
    self:log("Disabled logging for: " .. logType, "system")
end

-- Check if a log type is enabled
function Logger:isLogTypeEnabled(logType)
    return self.logTypes[logType] == true
end

-- Format timestamp
local function getTimestamp()
    return os.date("%Y-%m-%d %H:%M:%S")
end

-- Add log entry to buffer
function Logger:log(message, logType)
    logType = logType or self.LOG_TYPES.GENERAL

    -- Check if the log type is enabled before logging
    if not self:isLogTypeEnabled(logType) then
        return
    end

    local formattedLog = string.format(
        "[%s][%s] %s",
        getTimestamp(),
        logType:upper(),
        message
    )

    table.insert(self.logs, formattedLog)

    -- Print immediately for errors
    if logType == self.LOG_TYPES.ERROR then
        warn(formattedLog)
    else
        print(formattedLog)
    end

    -- Send logs when buffer reaches the max size
    if #self.logs >= self.maxBufferSize then
        self:flushLogs()
    end
end

-- Error logging helper
function Logger:error(message)
    self:log(message, self.LOG_TYPES.ERROR)
end

-- Debug logging helper
function Logger:debug(message)
    self:log(message, self.LOG_TYPES.DEBUG)
end

-- Send logs to heartbeat or external function
function Logger:flushLogs()
    if #self.logs == 0 then
        return
    end

    -- Here you could implement external logging service integration
    -- For now, we'll just clear the buffer
    self.logs = {}
end

-- Initialize logging system
function Logger:init()
    -- Enable default log types
    self:enableLogType(self.LOG_TYPES.GENERAL)
    self:enableLogType(self.LOG_TYPES.ERROR)
    self:enableLogType(self.LOG_TYPES.SYSTEM)

    -- Start periodic log flushing
    game:GetService("RunService").Heartbeat:Connect(function()
        self:flushLogs()
    end)

    self:log("Logging system initialized", self.LOG_TYPES.SYSTEM)
end

-- Initialize the logger
Logger:init()

return Logger 