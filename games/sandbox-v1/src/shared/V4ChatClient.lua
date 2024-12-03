-- V4ChatClient.lua
local V4ChatClient = {}

-- Import existing utilities/services
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local NPCConfig = require(ReplicatedStorage.NPCSystem.NPCConfig)
local ChatUtils = require(ReplicatedStorage.NPCSystem.ChatUtils)
local LettaConfig = require(ReplicatedStorage.NPCSystem.LettaConfig)

-- Configuration
local API_VERSION = "v4"
local FALLBACK_VERSION = "v3"
local LETTA_BASE_URL = LettaConfig.BASE_URL
local LETTA_ENDPOINT = LettaConfig.ENDPOINTS.CHAT
local ENDPOINTS = {
    CHAT = "/v4/chat",
    END_CONVERSATION = "/v4/conversations"
}

-- Adapter to convert V3 format to V4
local function adaptV3ToV4Request(v3Request)
    local is_new = not (v3Request.metadata and v3Request.metadata.conversation_id)
    return {
        message = v3Request.message,
        initiator_id = tostring(v3Request.player_id),
        target_id = v3Request.npc_id,
        conversation_type = "npc_user",
        system_prompt = v3Request.system_prompt,
        conversation_id = v3Request.metadata and v3Request.metadata.conversation_id,
        context = {
            initiator_name = v3Request.context.participant_name,
            target_name = v3Request.npc_name,
            is_new_conversation = is_new,
            nearby_players = v3Request.context.nearby_players or {},
            npc_location = v3Request.context.npc_location or "unknown"
        }
    }
end

-- Adapter to convert V4 response to V3 format
local function adaptV4ToV3Response(v4Response)
    return {
        message = v4Response.message,
        action = v4Response.action or {
            type = "none",
            data = {}
        },
        metadata = {
            conversation_id = v4Response.conversation_id,
            v4_metadata = v4Response.metadata
        }
    }
end

local function handleLettaChat(data)
    print("Attempting Letta chat first...")
    print("Incoming data:", HttpService:JSONEncode(data))

    local success, response = pcall(function()
        local lettaData = {
            npc_id = data.npc_id,
            participant_id = tostring(data.player_id),
            message = data.message
        }

        print("Sending to Letta - npc_id:", data.npc_id)
        print("Full Letta request:", HttpService:JSONEncode(lettaData))

        local jsonData = HttpService:JSONEncode(lettaData)
        local url = LETTA_BASE_URL .. LETTA_ENDPOINT
        print("Sending to URL:", url)
        local response = HttpService:PostAsync(
            url,
            jsonData,
            Enum.HttpContentType.ApplicationJson,
            false
        )
        
        print("Letta response:", response)
        local decoded = HttpService:JSONDecode(response)
        
        -- Fix action type format
        if decoded.action and decoded.action.type then
            decoded.action.type = "none"  -- Default to none if invalid
        end
        
        return decoded
    end)

    if success then
        if response.error then
            warn("Letta error:", HttpService:JSONEncode(response))
            return nil
        end

        print("Letta success:", HttpService:JSONEncode(response))
        return {
            message = response.message,
            action = response.action or { type = "none" },
            metadata = {
                conversation_id = response.conversation_id,
                v4_metadata = response.metadata
            }
        }
    else
        warn("Letta request failed:", response)
        return nil
    end
end

function V4ChatClient:SendMessageV4(originalRequest)
    local success, result = pcall(function()
        print("V4: Attempting to send message") -- Debug
        -- Convert V3 request format to V4
        local v4Request = adaptV3ToV4Request(originalRequest)
        
        -- Add action instructions to system prompt
        local actionInstructions = [[
            -- existing action instructions...
        ]]

        v4Request.system_prompt = (v4Request.system_prompt or "") .. actionInstructions
        print("V4: Converted request:", HttpService:JSONEncode(v4Request))
        
        local response = ChatUtils:MakeRequest(ENDPOINTS.CHAT, v4Request)
        print("V4: Got response:", HttpService:JSONEncode(response))
        
        return adaptV4ToV3Response(response)
    end)
    
    if not success then
        warn("V4 chat failed, falling back to V3:", result)
        return {
            success = false,
            shouldFallback = true,
            error = result
        }
    end
    
    return result
end

function V4ChatClient:SendMessage(originalRequest)
    print("V4ChatClient:SendMessage called")
    -- Try Letta first
    local lettaResponse = handleLettaChat(originalRequest)
    if lettaResponse then
        print("Letta response successful")
        return lettaResponse
    end

    print("Letta failed, falling back to V4")
    -- Fall back to V4 if Letta fails
    return self:SendMessageV4(originalRequest)
end

function V4ChatClient:EndConversation(conversationId)
    if not conversationId then return end
    
    local success, result = pcall(function()
        return ChatUtils:MakeRequest(
            ENDPOINTS.END_CONVERSATION .. "/" .. conversationId,
            nil,
            "DELETE"
        )
    end)
    
    if not success then
        warn("Failed to end V4 conversation:", result)
    end
end

-- Optional: Add V4-specific features while maintaining V3 compatibility
function V4ChatClient:GetConversationMetrics()
    local success, result = pcall(function()
        return ChatUtils:MakeRequest("/v4/metrics", nil, "GET")
    end)
    
    return success and result or nil
end

return V4ChatClient 