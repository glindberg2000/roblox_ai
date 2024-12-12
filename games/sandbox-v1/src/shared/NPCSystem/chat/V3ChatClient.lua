-- Basic V3 client for fallback
local V3ChatClient = {}

function V3ChatClient:SendMessage(request)
    -- Basic V3 implementation
    return {
        message = "V3 Fallback: " .. request.message,
        action = { type = "none" }
    }
end

return V3ChatClient 