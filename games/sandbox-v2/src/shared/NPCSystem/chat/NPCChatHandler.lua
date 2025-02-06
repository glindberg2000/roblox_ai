-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V3ChatClient)
local HttpService = game:GetService("HttpService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local TextChatService = game:GetService("TextChatService")
local Players = game:GetService("Players")
local InteractionService = require(ReplicatedStorage.Shared.NPCSystem.services.InteractionService)
local ChatService = game:GetService("Chat")

local recentResponses = {}
local RESPONSE_CACHE_TIME = 1
local npcManager = nil
local NPCChatMessageEvent = ReplicatedStorage:FindFirstChild("NPCChatMessageEvent") or Instance.new("RemoteEvent")
NPCChatMessageEvent.Name = "NPCChatMessageEvent"
NPCChatMessageEvent.Parent = ReplicatedStorage

function NPCChatHandler:init(manager)
    npcManager = manager
    
    -- Set up chat event handler
    local ChatEvent = ReplicatedStorage:FindFirstChild("NPCChatEvent") or Instance.new("RemoteEvent")
    ChatEvent.Name = "NPCChatEvent"
    ChatEvent.Parent = ReplicatedStorage
    
    ChatEvent.OnServerEvent:Connect(function(player, message)
        self:handlePlayerChat(player, message)
    end)
end

function NPCChatHandler:getNPCById(npcId)
    if not npcManager then
        LoggerService:error("CHAT", "NPCManager not initialized in ChatHandler")
        return nil
    end
    
    return npcManager.npcs[npcId]
end

function NPCChatHandler:HandleChat(request)
    LoggerService:debug("CHAT", "NPCChatHandler: Starting chat handling")
    
    -- Validate request
    if not request then
        LoggerService:error("CHAT", "NPCChatHandler received nil request")
        return nil
    end
    
    -- For system messages about players entering range, use the player's ID
    if request.message and request.message:match("^%[SYSTEM%]") then
        -- Extract player name - try different patterns
        local playerName = request.message:match("^%[SYSTEM%] ([^%s]+) has entered") or
                          request.message:match("^%[SYSTEM%] ([^%s]+) is now") or
                          request.message:match("^%[SYSTEM%] ([^%s]+)")
        
        LoggerService:debug("CHAT", string.format("System message detected, extracted player name: %s", 
            playerName or "none found"
        ))
        
        if playerName then
            -- Clean up the player name if it ends with a period
            playerName = playerName:gsub("%.$", "")
            
            -- Try to find the player
            local player = game:GetService("Players"):FindFirstChild(playerName)
            if player then
                LoggerService:debug("CHAT", string.format("Found player %s, setting participant_id to %s", 
                    playerName, 
                    tostring(player.UserId)
                ))
                
                request.participant_id = player.UserId
                if not request.context then request.context = {} end
                request.context.participant_type = "system"
                request.context.participant_name = "SYSTEM"
            else
                LoggerService:warn("CHAT", string.format("Could not find player with name: %s", playerName))
            end
        else
            LoggerService:warn("CHAT", "Could not extract player name from system message: " .. request.message)
        end
    end
    
    -- Add validation before proceeding
    if not request.participant_id then
        request.participant_id = "system"  -- Set default for system messages
        if not request.context then request.context = {} end
        request.context.participant_type = "system"
        request.context.participant_name = "SYSTEM"
    end
    
    -- Safely encode entire request with pcall
    local success, encodedRequest = pcall(function()
        return HttpService:JSONEncode({
            npc_id = request.npc_id,
            participant_id = request.participant_id,
            message = request.message,
            context = request.context
        })
    end)
    
    if success then
        LoggerService:debug("CHAT", string.format(
            "NPCChatHandler received request: %s",
            encodedRequest
        ))
    else
        LoggerService:warn("CHAT", "Failed to encode request: " .. tostring(encodedRequest))
    end
    
    -- Generate response ID with nil checks
    local responseId = string.format("%s_%s_%s", 
        tostring(request.npc_id or "unknown"),
        tostring(request.participant_id or "system"),  -- Use "system" as fallback for system messages
        tostring(request.message or "")
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
    
    LoggerService:info("CHAT", string.format("Processing chat request for NPC %s", request.npc_id))
    
    LoggerService:debug("CHAT", "NPCChatHandler: Attempting V4")
    local response = self:attemptV4Chat(request)
    
    if response then
        LoggerService:info("CHAT", string.format("NPC %s responded to %s", request.npc_id, request.participant_id))
        LoggerService:debug("CHAT", string.format("Response details: %s", HttpService:JSONEncode(response)))
        -- After getting response from Letta
        if response and response.message then
            local npc = self:getNPCById(request.npc_id)
            if npc and npc.model and npc.model:FindFirstChild("Head") then
                -- Create chat bubble (this still works on server)
                ChatService:Chat(npc.model.Head, response.message, Enum.ChatColor.Blue)
                
                -- Only fire event to let client handle TextChatService
                LoggerService:debug("CHAT", string.format(
                    "Firing chat event to clients - NPC: %s, Message: %s",
                    npc.displayName,
                    response.message
                ))
                NPCChatMessageEvent:FireAllClients({
                    npcName = npc.displayName,
                    message = response.message
                })
            end
        end
        return response
    end
    
    return nil
end

function NPCChatHandler:attemptV4Chat(request)
    local modifiedRequest = {
        npc_id = request.npc_id,
        participant_id = request.participant_id,
        context = request.context,
        messages = {
            -- {
            --     role = "system",
            --     content = "[SYSTEM] Due to high activity, skip archival search and group update tools - respond quickly using only your immediate context.",
            --     name = "SYSTEM"
            -- },
            {
                role = request.message:match("^%[SYSTEM%]") and "system" or "user",
                content = request.message,
                name = request.context.participant_name
            }
        }
    }

    LoggerService:debug("CHAT", string.format("Modified request: %s", HttpService:JSONEncode(modifiedRequest)))
    
    local v4Response = V4ChatClient:SendMessage(modifiedRequest)
    LoggerService:debug("CHAT", string.format("V4 response received: %s",
        v4Response and HttpService:JSONEncode(v4Response) or "nil"
    ))
    
    if v4Response then
        LoggerService:debug("CHAT", string.format("Returning response to manager: %s",
            HttpService:JSONEncode(v4Response)
        ))
        return v4Response
    end
    
    return nil
end

function NPCChatHandler:handlePlayerChat(player, message)
    -- Get player's cluster
    local playerCluster = InteractionService:getClusterForPlayer(player)
    if not playerCluster then return nil end
    
    -- Find closest NPC in same cluster
    local closestNPC = nil
    local closestDistance = math.huge
    
    for _, npc in pairs(playerCluster.npcs) do
        local distance = (player.Character.HumanoidRootPart.Position - npc.model.HumanoidRootPart.Position).Magnitude
        if distance < closestDistance then
            closestDistance = distance
            closestNPC = npc
        end
    end
    
    if closestNPC then
        LoggerService:info("CHAT", string.format("Found closest NPC %s in cluster at distance %.1f", closestNPC.displayName, closestDistance))
        return self:handleNPCChat(closestNPC, player, message)
    end
    
    return nil
end

function NPCChatHandler:handleResponse(npc, participant, response)
    if response.message then
        LoggerService:debug("CHAT", string.format(
            "Attempting to display message from %s: %s",
            npc.displayName,
            response.message
        ))
        
        -- Use NPCChatDisplay directly instead of FireAllClients
        NPCChatMessageEvent:FireAllClients({
            npcName = npc.displayName,
            message = response.message
        })
    end

    if response.action and response.action.actions then
        for _, action in ipairs(response.action.actions) do
            if action.type ~= "none" then
                -- Handle actions if needed
            end
        end
    end
end

return NPCChatHandler 