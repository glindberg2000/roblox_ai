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
    LoggerService:debug("CHAT", string.format(
        "NPCChatHandler received request: %s",
        HttpService:JSONEncode(request)
    ))
    
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
                -- Create chat bubble
                local Chat = game:GetService("Chat")
                Chat:Chat(npc.model.Head, response.message, Enum.ChatColor.Blue)
                
                -- Send to client to handle chat display
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

return NPCChatHandler 