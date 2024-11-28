local V4ChatClient = {}

-- Import existing utilities/services
local HttpService = game:GetService("HttpService")
local NPCConfig = require(script.Parent.NPCConfig)
local ChatUtils = require(script.Parent.ChatUtils)

-- Configuration
local API_VERSION = "v4"
local FALLBACK_VERSION = "v3"
local ENDPOINTS = {
    CHAT = "/v4/chat",
    END_CONVERSATION = "/v4/conversations"
}

-- Adapter to convert V3 format to V4
local function adaptV3ToV4Request(v3Request)
    return {
        message = v3Request.message,
        initiator_id = v3Request.player_id,
        target_id = v3Request.npc_id,
        conversation_type = "npc_user",
        system_prompt = v3Request.system_prompt,
        context = {
            initiator_name = v3Request.context.player_name,
            target_name = v3Request.npc_name,
            is_new_conversation = v3Request.context.is_new_conversation,
            -- Preserve other context fields
            nearby_players = v3Request.context.nearby_players,
            npc_location = v3Request.context.npc_location
        }
    }
end

-- Adapter to convert V4 response to V3 format
local function adaptV4ToV3Response(v4Response)
    return {
        message = v4Response.message,
        action = v4Response.action,
        -- Store conversation_id in metadata for future use
        metadata = {
            conversation_id = v4Response.conversation_id,
            v4_metadata = v4Response.metadata
        }
    }
end

function V4ChatClient:SendMessage(originalRequest)
    local success, result = pcall(function()
        -- Convert V3 request format to V4
        local v4Request = adaptV3ToV4Request(originalRequest)
        
        -- Add existing conversation ID if available
        if originalRequest.metadata and originalRequest.metadata.conversation_id then
            v4Request.conversation_id = originalRequest.metadata.conversation_id
        end
        
        -- Make API request using existing HTTP service
        local response = ChatUtils:MakeRequest(ENDPOINTS.CHAT, v4Request)
        
        -- Convert V4 response back to V3 format
        return adaptV4ToV3Response(response)
    end)
    
    if not success then
        warn("V4 chat failed, falling back to V3:", result)
        -- Return format that triggers fallback to V3
        return {
            success = false,
            shouldFallback = true,
            error = result
        }
    end
    
    return result
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