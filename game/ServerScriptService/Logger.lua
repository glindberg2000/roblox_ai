local Logger = {}

-- Keep track of enabled categories
local ENABLED_CATEGORIES = {
    ERROR = true,      -- Keep errors always enabled
    SYSTEM = true,     -- Keep core system messages
    ANIMATION = true,  -- Keep animation logs for debugging
    CHAT = true,       -- Keep chat logs
    
    -- Disable noisy categories
    RANGE = false,
    DEBUG = false, 
    MOVEMENT = false,
    INTERACTION = false,
    THREAD = false,
    STATE = false,
    DATABASE = false,
    ASSET = false,
    API = false,
    NPC = false
}

function Logger:log(category, message)
    -- Skip if category is disabled
    if not ENABLED_CATEGORIES[category] then
        return
    end

    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    print(string.format("[%s] [%s] %s - Server - Logger", timestamp, category, message))
end

function Logger:error(message)
    self:log("ERROR", message)
end

function Logger:warn(message)
    self:log("WARN", message)
end

function Logger:debug(message)
    self:log("DEBUG", message)
end

function Logger:isCategoryEnabled(category)
    return ENABLED_CATEGORIES[category] == true
end

function Logger:setCategory(category, enabled)
    if ENABLED_CATEGORIES[category] ~= nil then
        ENABLED_CATEGORIES[category] = enabled
        self:log("SYSTEM", string.format("Logging category %s %s", 
            category,
            enabled and "enabled" or "disabled"
        ))
    end
end

function Logger:getEnabledCategories()
    local enabled = {}
    for category, isEnabled in pairs(ENABLED_CATEGORIES) do
        if isEnabled then
            table.insert(enabled, category)
        end
    end
    return enabled
end

return Logger 