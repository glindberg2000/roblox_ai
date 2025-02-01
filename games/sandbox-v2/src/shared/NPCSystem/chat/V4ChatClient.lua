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
    CHAT = LETTA_ENDPOINT,
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
    local lettaData = {
        npc_id = data.npc_id,
        participant_id = tostring(data.participant_id),
        messages = data.messages,
        context = data.context
    }

    local success, response = pcall(function()
        local jsonData = HttpService:JSONEncode(lettaData)
        local url = LETTA_BASE_URL .. LETTA_ENDPOINT
        local result = HttpService:PostAsync(url, jsonData, Enum.HttpContentType.ApplicationJson, false)
        return result
    end)

    if not success then
        LoggerService:error("CHAT", string.format("HTTP request failed: %s", response))
        return nil
    end

    local success2, decoded = pcall(HttpService.JSONDecode, HttpService, response)
    if not success2 then
        LoggerService:error("CHAT", string.format("JSON decode failed: %s", decoded))
        return nil
    end

    -- Log the full API response at INFO level
    LoggerService:info("API", string.format("Letta response: %s", response))

    -- Process actions array if present
    if decoded.action and decoded.action.actions then
        local ActionService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.ActionService)
        local NPCManagerV3 = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.NPCManagerV3)
        
        for _, action in ipairs(decoded.action.actions) do
            if action.type and action.data then
                -- Get the manager instance
                local manager = NPCManagerV3.getInstance()
                -- Get NPC using the manager's method for getting NPCs
                local npc = manager.npcs[data.npc_id]
                
                if npc then
                    -- Call existing ActionService methods
                    if ActionService[action.type] then
                        LoggerService:debug("ACTION", string.format("Executing action: %s for NPC %s", action.type, npc.displayName))
                        ActionService[action.type](npc, action.data)
                    else
                        LoggerService:warn("ACTION", string.format("Unknown action type '%s' - available actions: %s", 
                            action.type,
                            table.concat(table.keys(ActionService), ", ")
                        ))
                    end
                else
                    LoggerService:warn("ACTION", string.format("Could not find NPC with id %s", data.npc_id))
                end
            end
        end
    end

    return decoded
end

function V4ChatClient:SendMessageV4(originalRequest)
    local success, result = pcall(function()
        LoggerService:debug("CHAT", "V4: Attempting to send message")
        -- Convert V3 request format to V4
        local v4Request = adaptV3ToV4Request(originalRequest)
        
        -- Add action instructions to system prompt
        local actionInstructions = NPC_SYSTEM_PROMPT_ADDITION

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
    LoggerService:info("CHAT", string.format("Chat request from %s to %s", data.context.speaker_name, data.context.participant_name))
    
    -- Try Letta first
    local lettaResponse = handleLettaChat(data)
    if lettaResponse then
        return lettaResponse
    end

    LoggerService:warn("CHAT", "Letta chat attempt failed")
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