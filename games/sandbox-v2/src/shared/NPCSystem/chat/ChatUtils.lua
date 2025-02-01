local ChatUtils = {}

local HttpService = game:GetService("HttpService")
local API_BASE_URL = "https://roblox.ella-ai-care.com"

function ChatUtils:MakeRequest(endpoint, payload, method)
    method = method or (payload and "POST" or "GET")
    
    local requestConfig = {
        Url = API_BASE_URL .. endpoint,
        Method = method,
        Headers = {
            ["Content-Type"] = "application/json"
        }
    }
    
    if payload then
        requestConfig.Body = HttpService:JSONEncode(payload)
    end
    
    local success, response = pcall(function()
        return HttpService:RequestAsync(requestConfig)
    end)
    
    if success and response.Success then
        local decoded = HttpService:JSONDecode(response.Body)
        LoggerService:debug("API", string.format("Raw API response: %s", response.Body))
        LoggerService:debug("API", string.format("Decoded response: %s", HttpService:JSONEncode(decoded)))
        if decoded and not decoded.action then
            decoded.action = {
                type = "none",
                data = {}
            }
        end
        return decoded
    else
        warn("API request failed:", response.StatusCode, response.StatusMessage)
        warn("Request URL:", requestConfig.Url)
        warn("Request payload:", requestConfig.Body)
        if response.Body then
            warn("Response body:", response.Body)
        end
        error("Failed to make API request: " .. tostring(response.StatusMessage))
    end
end

return ChatUtils 