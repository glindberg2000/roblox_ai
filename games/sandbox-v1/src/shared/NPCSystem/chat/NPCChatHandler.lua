-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V3ChatClient)
local HttpService = game:GetService("HttpService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

function NPCChatHandler:HandleChat(request)
    LoggerService:debug("CHAT", string.format("NPCChatHandler: Received request %s", 
        HttpService:JSONEncode(request)))
    
    LoggerService:debug("CHAT", "NPCChatHandler: Attempting V4")
    local response = self:attemptV4Chat(request)
    
    if response then
        LoggerService:debug("CHAT", string.format("NPCChatHandler: V4 succeeded %s", 
            HttpService:JSONEncode(response)))
        return response
    end
    
    return nil
end

function NPCChatHandler:attemptV4Chat(request)
    local v4Response = V4ChatClient:SendMessage(request)
    
    if v4Response then
        -- Ensure we have a valid message
        if not v4Response.message then
            v4Response.message = "..."
        end
        return v4Response
    end
    
    -- If V4 failed, return error response
    return {
        message = "...",
        action = { type = "none" },
        metadata = {}
    }
end

return NPCChatHandler 