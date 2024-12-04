-- Logger.lua
local Logger = {
    LogLevel = {
        DEBUG = 1,
        INFO = 2,
        WARN = 3,
        ERROR = 4
    },
    currentLevel = 1,  -- Default to DEBUG
    categoryFilters = {
        -- System & Debug
        SYSTEM = true,
        DEBUG = true,
        ERROR = true,
        
        -- NPC Behavior
        VISION = false,
        MOVEMENT = true,
        ACTION = true,
        ANIMATION = true,
        
        -- Interaction & Chat
        CHAT = true,
        INTERACTION = true,
        RESPONSE = true,
        
        -- State & Data
        STATE = true,
        DATABASE = true,
        ASSET = true,
        API = true,
    }
}

function Logger:log(category, message)
    if self.categoryFilters[category] == false then
        return
    end
    
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    print(string.format("[%s] [%s] %s", timestamp, category:upper(), message))
end

return Logger