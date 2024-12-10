-- Logger.lua
local Logger = {
    LogLevel = {
        DEBUG = 1,
        INFO = 2,
        WARN = 3,
        ERROR = 4
    },
    currentLevel = 4,  -- Only show errors
    categoryFilters = {
        -- System & Debug
        SYSTEM = false,
        DEBUG = false,
        ERROR = true,    -- Keep only errors
        
        -- NPC Behavior (all disabled)
        VISION = false,
        MOVEMENT = false,
        ACTION = false,
        ANIMATION = false,
        
        -- Interaction & Chat (all disabled)
        CHAT = false,
        INTERACTION = false,
        RESPONSE = false,
        RANGE = false,   -- Disable range checking logs
        
        -- State & Data (all disabled)
        STATE = false,
        DATABASE = false,
        ASSET = false,
        API = false,
        NPC = false
    }
}

-- Add message queue to batch logs
local messageQueue = {}
local MAX_QUEUE_SIZE = 10
local FLUSH_INTERVAL = 1 -- Flush every second

function Logger:log(category, message)
    -- Only log if category is enabled
    if self.categoryFilters[category] == false then
        return
    end
    
    -- For errors, log immediately
    if category == "ERROR" then
        local timestamp = os.date("%H:%M:%S")
        print(string.format("[%s] [%s] %s", timestamp, category:upper(), message))
        return
    end
    
    -- Queue other messages
    table.insert(messageQueue, {
        timestamp = os.date("%H:%M:%S"),
        category = category,
        message = message
    })
    
    -- Flush if queue is full
    if #messageQueue >= MAX_QUEUE_SIZE then
        self:flushQueue()
    end
end

function Logger:flushQueue()
    for _, msg in ipairs(messageQueue) do
        print(string.format("[%s] [%s] %s", 
            msg.timestamp, 
            msg.category:upper(), 
            msg.message))
    end
    messageQueue = {}
end

-- Start periodic flush
task.spawn(function()
    while true do
        task.wait(FLUSH_INTERVAL)
        Logger:flushQueue()
    end
end)

return Logger