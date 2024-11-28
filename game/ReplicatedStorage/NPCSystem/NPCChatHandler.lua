local NPCChatHandler = {}

local V4ChatClient = require(script.Parent.V4ChatClient)
local V3ChatClient = require(script.Parent.V3ChatClient)

function NPCChatHandler:HandleChat(request)
    -- Try V4 first
    local response = V4ChatClient:SendMessage(request)
    
    -- Fall back to V3 if needed
    if not response.success and response.shouldFallback then
        return V3ChatClient:SendMessage(request)
    end
    
    return response
end

return NPCChatHandler 