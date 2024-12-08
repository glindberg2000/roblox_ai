-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.NPCSystem.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.NPCSystem.V3ChatClient)
local HttpService = game:GetService("HttpService")

function NPCChatHandler:HandleChat(request)
    print("NPCChatHandler: Received request", HttpService:JSONEncode(request))
    
    -- Try V4 first
    print("NPCChatHandler: Attempting V4")
    local v4Response = V4ChatClient:SendMessage(request)
    
    if v4Response then
        print("NPCChatHandler: V4 succeeded", HttpService:JSONEncode(v4Response))
        -- Ensure we have a valid message
        if not v4Response.message then
            v4Response.message = "I'm having trouble understanding right now."
        end
        return v4Response
    end
    
    -- If V4 failed, return error response
    print("NPCChatHandler: V4 failed, returning error response")
    return {
        message = "I'm having trouble understanding right now.",
        action = { type = "none" },
        metadata = {}
    }
end

return NPCChatHandler 