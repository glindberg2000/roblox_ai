local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.NPCSystem.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.NPCSystem.V3ChatClient)
local HttpService = game:GetService("HttpService")

function NPCChatHandler:HandleChat(request)
    print("NPCChatHandler: Received request", HttpService:JSONEncode(request))
    
    -- Try V4 first
    print("NPCChatHandler: Attempting V4")
    local response = V4ChatClient:SendMessage(request)
    
    -- Fall back to V3 if needed
    if not response.success and response.shouldFallback then
        print("NPCChatHandler: Falling back to V3", response.error)
        return V3ChatClient:SendMessage(request)
    end
    
    print("NPCChatHandler: V4 succeeded", HttpService:JSONEncode(response))
    return response
end

return NPCChatHandler 