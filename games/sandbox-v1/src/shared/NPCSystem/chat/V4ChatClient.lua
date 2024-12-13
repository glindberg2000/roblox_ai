-- V4ChatClient.lua
local V4ChatClient = {}

-- Import existing utilities/services
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local NPCConfig = require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)
local ChatUtils = require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)
local LettaConfig = require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Configuration
local API_VERSION = "v4"
local FALLBACK_VERSION = "v3"
local LETTA_BASE_URL = LettaConfig.BASE_URL
local LETTA_ENDPOINT = LettaConfig.ENDPOINTS.CHAT
local ENDPOINTS = {
    CHAT = "/v4/chat",
    END_CONVERSATION = "/v4/conversations"
}

-- Track conversation history
local conversationHistory = {}

local function getConversationKey(npc_id, participant_id)
    return npc_id .. "_" .. participant_id
end

local function addToHistory(npc_id, participant_id, message, sender)
    local key = getConversationKey(npc_id, participant_id)
    conversationHistory[key] = conversationHistory[key] or {}
    
    table.insert(conversationHistory[key], {
        message = message,
        sender = sender,
        timestamp = os.time()
    })
    
    -- Keep last 10 messages
    while #conversationHistory[key] > 10 do
        table.remove(conversationHistory[key], 1)
    end
end

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
    LoggerService:debug("CHAT", "V4ChatClient: Attempting Letta chat first...")
    LoggerService:debug("CHAT", string.format("V4ChatClient: Raw incoming data: %s", HttpService:JSONEncode(data)))
    
    local participantType = (data.context and data.context.participant_type) or data.participant_type or "player"
    LoggerService:debug("CHAT", string.format("V4ChatClient: Determined participant type: %s", participantType))
    
    local convKey = getConversationKey(data.npc_id, data.participant_id)
    local history = conversationHistory[convKey] or {}
    
    if #history >= 5 then  -- After 5 messages
        return {
            message = "I've got to run now! Thanks for the chat! See you later! 👋",
            action = { type = "none" },
            metadata = {
                participant_type = "npc",
                is_npc_chat = true,
                should_end = true  -- Signal to end conversation
            }
        }
    end
    
    addToHistory(data.npc_id, data.participant_id, data.message, data.context.participant_name)
    
    local lettaData = {
        npc_id = data.npc_id,
        participant_id = tostring(data.participant_id),
        message = data.message,
        participant_type = participantType,
        context = {
            participant_type = participantType,
            participant_name = data.context and data.context.participant_name,
            interaction_history = history,
            nearby_players = data.context and data.context.nearby_players or {},
            npc_location = data.context and data.context.npc_location or "Unknown",
            is_new_conversation = #history == 1  -- Only new if this is first message
        }
    }

    LoggerService:debug("CHAT", string.format("V4ChatClient: Final Letta request: %s", HttpService:JSONEncode(lettaData)))
    
    local success, response = pcall(function()
        local jsonData = HttpService:JSONEncode(lettaData)
        local url = LETTA_BASE_URL .. LETTA_ENDPOINT
        LoggerService:debug("CHAT", string.format("V4ChatClient: Sending to URL: %s", url))
        return HttpService:PostAsync(url, jsonData, Enum.HttpContentType.ApplicationJson, false)
    end)
    
    if not success then
        LoggerService:warn("CHAT", string.format("HTTP request failed: %s", response))
        return nil
    end
    
    LoggerService:debug("CHAT", string.format("V4ChatClient: Raw Letta response: %s", response))
    local success2, decoded = pcall(HttpService.JSONDecode, HttpService, response)
    if not success2 then
        warn("JSON decode failed:", decoded)
        return nil
    end
    
    return decoded
end

function V4ChatClient:SendMessageV4(originalRequest)
    local success, result = pcall(function()
        LoggerService:debug("CHAT", "V4: Attempting to send message")
        -- Convert V3 request format to V4
        local v4Request = adaptV3ToV4Request(originalRequest)
        
        -- Add action instructions to system prompt
        local actionInstructions = [[
            -- existing action instructions...
        ]]

        v4Request.system_prompt = (v4Request.system_prompt or "") .. actionInstructions
        LoggerService:debug("CHAT", string.format("V4: Converted request: %s", HttpService:JSONEncode(v4Request)))
        
        local response = ChatUtils:MakeRequest(ENDPOINTS.CHAT, v4Request)
        LoggerService:debug("CHAT", string.format("V4: Got response: %s", HttpService:JSONEncode(response)))
        
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

function V4ChatClient:SendMessage(data)
    LoggerService:debug("CHAT", "V4ChatClient: SendMessage called")
    -- Try Letta first
    local lettaResponse = handleLettaChat(data)
    if lettaResponse then
        return lettaResponse
    end

    LoggerService:debug("CHAT", "Letta failed - returning nil")
    return nil
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