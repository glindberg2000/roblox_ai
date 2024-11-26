-- Logger.lua
local Logger = {}

function Logger:log(category, message, ...)
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

-- Add convenience methods for each category
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

return Logger