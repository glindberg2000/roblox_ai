-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient)
local HttpService = game:GetService("HttpService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

function NPCChatHandler:HandleChat(request)
    LoggerService:debug("CHAT", string.format("NPCChatHandler: Received request %s", 
        HttpService:JSONEncode(request)))
    
    LoggerService:debug("CHAT", "NPCChatHandler: Attempting V4")
    local response = self:attemptV4Chat(request)
    
    if response then
        -- Log full response for debugging
        LoggerService:debug("CHAT", string.format("NPCChatHandler: Raw V4 response: %s",
            HttpService:JSONEncode(response)))
            
        -- Ensure we have a valid message
        if not response.message then
            response.message = "I'm having trouble responding right now."
            LoggerService:warn("CHAT", "Missing message in response")
        end
        
        -- Handle navigation action
        if response.action and response.action.type == "navigate" then
            -- Extract coordinates from action data
            local coords = response.action.data.coordinates
            if coords then
                LoggerService:debug("CHAT", string.format(
                    "Navigation coordinates extracted: x=%.1f, y=%.1f, z=%.1f",
                    coords.x, coords.y, coords.z
                ))
            else
                LoggerService:warn("CHAT", "Missing coordinates in navigation action")
            end
        end
        
        return response
    end
    
    LoggerService:warn("CHAT", "V4 chat failed, returning error response")
    return {
        message = "I'm having trouble understanding right now.",
        action = { type = "none" },
        metadata = {
            error = "Chat failed"
        }
    }
end

function NPCChatHandler:attemptV4Chat(request)
    LoggerService:debug("CHAT", "Sending request to V4ChatClient")
    local v4Response = V4ChatClient:SendMessage(request)
    
    if v4Response then
        LoggerService:debug("CHAT", string.format("Got V4 response: %s",
            HttpService:JSONEncode(v4Response)))
        return v4Response
    end
    
    LoggerService:warn("CHAT", "V4ChatClient returned nil response")
    return nil
end

return NPCChatHandler 