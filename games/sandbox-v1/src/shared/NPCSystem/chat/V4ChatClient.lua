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
    print("Attempting Letta chat first...")
    print("Raw incoming data:", HttpService:JSONEncode(data))
    
    -- Get participant type from context or data
    local participantType = (data.context and data.context.participant_type) or data.participant_type or "player"
    print("Determined participant type:", participantType)
    
    -- Get conversation key and history
    local convKey = getConversationKey(data.npc_id, data.participant_id)
    local history = conversationHistory[convKey] or {}
    
    -- Check if conversation has gone on too long
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
    
    -- Add current message to history
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

    print("Final Letta request:", HttpService:JSONEncode(lettaData))
    
    local success, response = pcall(function()
        local jsonData = HttpService:JSONEncode(lettaData)
        local url = LETTA_BASE_URL .. LETTA_ENDPOINT
        print("Sending to URL:", url)
        return HttpService:PostAsync(
            url,
            jsonData,
            Enum.HttpContentType.ApplicationJson,
            false
        )
    end)
    
    if not success then
        warn("HTTP request failed:", response)
        return nil
    end
    
    print("Raw Letta response:", response)
    local success2, decoded = pcall(HttpService.JSONDecode, HttpService, response)
    if not success2 then
        warn("JSON decode failed:", decoded)
        return nil
    end
    
    return decoded
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

function V4ChatClient:SendMessage(data)
    print("V4ChatClient:SendMessage called")
    -- Try Letta first
    local lettaResponse = handleLettaChat(data)
    if lettaResponse then
        return lettaResponse
    end

    -- Return nil on failure to prevent error message loops
    print("Letta failed - returning nil")
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