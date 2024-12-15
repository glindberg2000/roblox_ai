-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V3ChatClient)
local HttpService = game:GetService("HttpService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

local recentResponses = {}
local RESPONSE_CACHE_TIME = 1

function NPCChatHandler:HandleChat(request)
    -- Generate response ID
    local responseId = string.format("%s_%s_%s", 
        request.npc_id,
        request.participant_id,
        request.message
    )
    
    -- Check for duplicate response
    if recentResponses[responseId] then
        if tick() - recentResponses[responseId] < RESPONSE_CACHE_TIME then
            return nil -- Skip duplicate response
        end
    end
    
    -- Store response timestamp
    recentResponses[responseId] = tick()
    
    -- Clean up old responses
    for id, timestamp in pairs(recentResponses) do
        if tick() - timestamp > RESPONSE_CACHE_TIME then
            recentResponses[id] = nil
        end
    end
    
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