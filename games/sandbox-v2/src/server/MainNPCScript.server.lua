-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)
local InteractionService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.InteractionService)
local TextChatService = game:GetService("TextChatService")
local ChatService = game:GetService("Chat")
local HttpService = game:GetService("HttpService")

local success, result = pcall(function()
	return require(ServerScriptService:WaitForChild("InteractionController", 5))
end)

if success then
	InteractionController = result
	LoggerService:info("SYSTEM", "InteractionController loaded successfully")
else
	LoggerService:error("ERROR", "Failed to load InteractionController: " .. tostring(result))
	-- Provide a basic implementation to prevent further errors
	InteractionController = {
		new = function()
			return {
				canInteract = function()
					return true
				end,
				startInteraction = function()
					return true
				end,
				endInteraction = function() end,
				getInteractingNPC = function()
					return nil
				end,
			}
		end,
	}
end

-- Rest of your MainNPCScript code...
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")

local Logger = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Move ensureStorage to the top, before NPC initialization
local function ensureStorage()
    local ServerStorage = game:GetService("ServerStorage")
    
    -- Ensure Assets folder exists (managed by Rojo)
    local Assets = ServerStorage:FindFirstChild("Assets")
    if not Assets or not Assets:IsA("Folder") then
        error("Assets folder not found in ServerStorage! Check Rojo sync.")
    end
    
    -- Ensure npcs folder exists within Assets (managed by Rojo)
    local npcs = Assets:FindFirstChild("npcs")
    if not npcs or not npcs:IsA("Folder") then
        error("npcs folder not found in Assets! Check Rojo sync.")
    end
    
    Logger:log("SYSTEM", "Storage structure verified")
end

-- Call ensureStorage first
ensureStorage()

-- Then initialize NPC system
local NPCManagerV3 = require(ReplicatedStorage.Shared.NPCSystem.NPCManagerV3)
LoggerService:info("SYSTEM", "Starting NPC initialization")
local npcManagerV3 = NPCManagerV3.new()
local interactionService = InteractionService.new(npcManagerV3)  -- Create instance with npcManager
LoggerService:info("SYSTEM", "NPC Manager created")

-- Debug NPC abilities
for npcId, npcData in pairs(npcManagerV3.npcs) do
	LoggerService:debug("NPC", string.format("NPC %s abilities: %s", 
		npcData.displayName,
		table.concat(npcData.abilities or {}, ", ")
	))
end

for npcId, npcData in pairs(npcManagerV3.npcs) do
	LoggerService:info("STATE", string.format("NPC spawned: %s", npcData.displayName))
end

local interactionController = npcManagerV3.interactionController

LoggerService:info("SYSTEM", "NPC system V3 initialized")

-- Add cooldown tracking
local GREETING_COOLDOWN = 60 -- 60 seconds between greetings
local ENTRY_COOLDOWN = 300 -- 5 minutes between entry notifications
local greetingCooldowns = {} -- Track when NPCs last greeted each other
local entryNotificationCooldowns = {} -- Track when NPCs were last notified about a player

-- Add at the top with other state variables
-- local activeConversations = { ... }

-- Add near the top with other requires
local LettaConfig = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.config.LettaConfig)

-- Add new function for group updates
local function updateNPCGroup(npc, player, isJoining)
    -- Log before HTTP call
    LoggerService:debug("GROUP", string.format(
        "Sending group update - URL: %s, Data: %s",
        LettaConfig.BASE_URL .. LettaConfig.ENDPOINTS.GROUP_UPDATE,
        HttpService:JSONEncode({
            npc_id = npc.id,
            player_id = tostring(player.UserId),
            is_joining = isJoining,
            player_name = player.Name
        })
    ))

    local success, response = pcall(function()
        return HttpService:PostAsync(
            LettaConfig.BASE_URL .. LettaConfig.ENDPOINTS.GROUP_UPDATE,
            HttpService:JSONEncode({
                npc_id = npc.id,
                player_id = tostring(player.UserId),
                is_joining = isJoining,
                player_name = player.Name
            }),
            Enum.HttpContentType.ApplicationJson,
            false,
            LettaConfig.DEFAULT_HEADERS
        )
    end)

    if not success then
        LoggerService:error("GROUP", string.format(
            "Failed to update group for %s: %s",
            npc.displayName,
            tostring(response)
        ))
    else
        LoggerService:debug("GROUP", string.format(
            "Group update for %s: %s %s group",
            npc.displayName,
            player.Name,
            isJoining and "joined" or "left"
        ))
    end
end

local function checkPlayerProximity(clusters)
    for _, cluster in ipairs(clusters) do
        if cluster.players > 0 and cluster.npcs > 0 then
            for _, playerName in ipairs(cluster.members) do
                local player = Players:FindFirstChild(playerName)
                if player then
                    for _, npcName in ipairs(cluster.members) do
                        local npc = nil
                        for _, possibleNpc in pairs(npcManagerV3.npcs) do
                            if possibleNpc.displayName == npcName then
                                npc = possibleNpc
                                break
                            end
                        end

                        if npc and interactionController:canInteract(player) then
                            -- Check entry notification cooldown
                            local entryKey = npc.id .. "_entry_" .. player.UserId
                            local lastEntry = entryNotificationCooldowns[entryKey]
                            
                            if not lastEntry or (os.time() - lastEntry) > ENTRY_COOLDOWN then
                                -- Update group membership first
                                updateNPCGroup(npc, player, true)

                                -- Get list of all members in speaking range
                                local npcsInRange = {}
                                local playersInRange = {}
                                for _, memberName in ipairs(cluster.members) do
                                    if memberName ~= npc.displayName then  -- Exclude self
                                        local isNPC = false
                                        for _, otherNpc in pairs(npcManagerV3.npcs) do
                                            if otherNpc.displayName == memberName then
                                                table.insert(npcsInRange, memberName)
                                                isNPC = true
                                                break
                                            end
                                        end
                                        if not isNPC then
                                            table.insert(playersInRange, memberName)
                                        end
                                    end
                                end

                                -- Create enhanced system message
                                local systemMessage = string.format(
                                    "[SYSTEM] %s has entered your range. You are now in speaking range with %s%s%s.",
                                    player.Name,
                                    #npcsInRange > 0 and table.concat(npcsInRange, ", ") or "no other NPCs",
                                    #playersInRange > 0 and (#npcsInRange > 0 and " and " or "") or "",
                                    #playersInRange > 0 and table.concat(playersInRange, ", ") or ""
                                )

                                -- Add structured data for API
                                local context = {
                                    update_type = "group_membership",
                                    action = "join",
                                    group = {
                                        npcs = npcsInRange,
                                        players = playersInRange,
                                        location = player.Character and player.Character.PrimaryPart and {
                                            x = player.Character.PrimaryPart.Position.X,
                                            y = player.Character.PrimaryPart.Position.Y,
                                            z = player.Character.PrimaryPart.Position.Z
                                        } or nil
                                    }
                                }

                                LoggerService:debug("GROUP", string.format(
                                    "Group update - NPC: %s, Player: %s, Members: %s",
                                    npc.displayName,
                                    player.Name,
                                    HttpService:JSONEncode(context.group)
                                ))

                                -- Handle interaction after group update
                                npcManagerV3:handleNPCInteraction(npc, player, systemMessage, context)
                                entryNotificationCooldowns[entryKey] = os.time()
                            end
                            
                            greetingCooldowns[cooldownKey] = os.time()
                        end
                    end
                end
            end
        end
    end
end

-- Move this function up, before onPlayerChatted
local function handleChatRequest(player)
    LoggerService:debug("CHAT", "Handling chat request for " .. player.Name)
    
    local playerPosition = player.Character and player.Character.PrimaryPart
    if not playerPosition then 
        LoggerService:warn("CHAT", "No valid position for player " .. player.Name)
        return 
    end

    -- Use existing cluster system
    local clusters = interactionService:getLatestClusters()
    LoggerService:debug("CHAT", string.format("Found %d clusters", #clusters))
    
    -- Find which cluster the player is in
    local playerCluster = nil
    for _, cluster in ipairs(clusters) do
        if table.find(cluster.members, player.Name) then
            playerCluster = cluster
            LoggerService:debug("CHAT", string.format("Found player in cluster with %d members", #cluster.members))
            break
        end
    end

    -- If player isn't in a cluster, they can't interact
    if not playerCluster then 
        LoggerService:warn("CHAT", "Player not in any cluster")
        return 
    end

    -- Find closest NPC that's in the same cluster
    local closestNPC, closestDistance = nil, math.huge
    for _, npc in pairs(npcManagerV3.npcs) do
        if npc.model and npc.model.PrimaryPart then
            -- Check if NPC is in same cluster as player
            if table.find(playerCluster.members, npc.displayName) then
                local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
                LoggerService:debug("CHAT", string.format("Found NPC %s at distance %.1f", npc.displayName, distance))
                if distance < closestDistance and not npc.isInteracting then
                    closestNPC, closestDistance = npc, distance
                end
            end
        end
    end

    if not closestNPC then
        LoggerService:warn("CHAT", "No eligible NPC found in cluster")
    end

    return closestNPC, closestDistance
end

-- Add this helper function near the top
local function createPlayerParticipant(player)
    return {
        GetParticipantType = function()
            return "Player"
        end,
        GetUserId = function()
            return player.UserId
        end,
        GetName = function()
            return player.Name
        end,
        GetParticipantId = function()
            return tostring(player.UserId)
        end,
        GetInteractionHistory = function()
            return {}
        end,
        Name = player.Name,
        _player = player
    }
end

-- Then modify onPlayerChatted to wrap the player
local function onPlayerChatted(player, message)
    LoggerService:info("CHAT", string.format("[onPlayerChatted] Called with player: %s, message: %s", 
        player.Name, message))
        
    -- Find closest NPC to handle the chat
    local closestNPC, closestDistance = handleChatRequest(player)
    if closestNPC then
        LoggerService:info("CHAT", string.format("Found closest NPC %s at distance %0.1f", 
            closestNPC.displayName, closestDistance))
            
        -- Debug NPC methods
        LoggerService:debug("CHAT", string.format("NPC methods: %s",
            HttpService:JSONEncode({
                hasGetInteractionHistory = type(closestNPC.getInteractionHistory) == "function",
                hasGetInteractionHistoryCaps = type(closestNPC.GetInteractionHistory) == "function"
            })
        ))
            
        -- Create participant wrapper for the player
        local playerParticipant = createPlayerParticipant(player)
            
        -- Have the NPC handle the chat message with wrapped player
        npcManagerV3:handleChat(closestNPC, playerParticipant, message)
    end
end

-- Debug chat system status immediately
LoggerService:info("CHAT", string.format(
    "Chat System Status:\nTextChat Enabled: %s\nLegacy Chat Enabled: %s",
    tostring(TextChatService.ChatVersion == Enum.ChatVersion.TextChatService),
    tostring(ChatService.LoadDefaultChat)
))

-- Set up chat before anything else
local function setupChatConnections()
    LoggerService:info("CHAT", "Setting up chat connections")
    
    if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
        LoggerService:info("CHAT", string.format("Chat version: %s", tostring(TextChatService.ChatVersion)))
        
        -- Wait for and connect to the general channel
        local success, result = pcall(function()
            local channels = TextChatService:WaitForChild("TextChannels", 10)
            if not channels then
                LoggerService:error("CHAT", "Failed to find TextChannels after 10 seconds")
                return
            end
            
            local generalChannel = channels:WaitForChild("RBXGeneral", 10)
            if not generalChannel then
                LoggerService:error("CHAT", "Failed to find RBXGeneral channel after 10 seconds")
                return
            end
            
            LoggerService:info("CHAT", "Found general chat channel")
            
            -- Set up the ShouldDeliverCallback
            generalChannel.ShouldDeliverCallback = function(message, userId)
                LoggerService:info("CHAT", "ShouldDeliverCallback fired")
                
                -- Debug the raw message
                LoggerService:info("CHAT", string.format("Raw message data: %s", 
                    HttpService:JSONEncode({
                        Text = message.Text,
                        TextSource = message.TextSource and {
                            UserId = message.TextSource.UserId,
                            Name = message.TextSource.Name
                        },
                        TargetUserId = userId
                    })
                ))
                
                local player = Players:GetPlayerByUserId(message.TextSource.UserId)
                if player then
                    LoggerService:info("CHAT", string.format("Received message from %s: %s",
                        player.Name, message.Text))
                    onPlayerChatted(player, message.Text)
                else
                    LoggerService:warn("CHAT", "Could not find player for UserId: " .. tostring(message.TextSource.UserId))
                end
                
                -- Always deliver the message
                return true
            end
            
            LoggerService:info("CHAT", "ShouldDeliverCallback handler established")
        end)
        
        if not success then
            LoggerService:error("CHAT", "Failed to set up chat connection: " .. tostring(result))
        end
    else
        LoggerService:warn("CHAT", "TextChatService not enabled, using legacy chat")
        -- Legacy chat system
        
        -- Connect to existing players
        for _, player in ipairs(Players:GetPlayers()) do
            LoggerService:info("CHAT", "Setting up legacy chat for: " .. player.Name)
            player.Chatted:Connect(function(message)
                LoggerService:info("CHAT", string.format("Legacy chat from %s: %s", 
                    player.Name, message))
                onPlayerChatted(player, message)
            end)
        end
        
        -- Connect to new players
        Players.PlayerAdded:Connect(function(player)
            LoggerService:info("CHAT", "Setting up legacy chat for new player: " .. player.Name)
            player.Chatted:Connect(function(message)
                LoggerService:info("CHAT", string.format("Legacy chat from %s: %s", 
                    player.Name, message))
                onPlayerChatted(player, message)
            end)
        end)
    end
end

-- Call setup immediately
setupChatConnections()

function checkNPCProximity(clusters)
    for _, cluster in ipairs(clusters) do
        if cluster.npcs >= 2 then
            for i, npc1Name in ipairs(cluster.members) do
                local npc1 = nil
                for _, npc in pairs(npcManagerV3.npcs) do
                    if npc.displayName == npc1Name then
                        npc1 = npc
                        break
                    end
                end
                
                -- Remove isInteracting check
                if npc1 then
                    for j = i + 1, #cluster.members do
                        local npc2Name = cluster.members[j]
                        local npc2 = nil
                        for _, npc in pairs(npcManagerV3.npcs) do
                            if npc.displayName == npc2Name then
                                npc2 = npc
                                break
                            end
                        end
                        
                        -- Remove all conversation locks
                        if npc2 then
                            -- Only check cooldown
                            local cooldownKey = npc1.id .. "_" .. npc2.id
                            local lastGreeting = greetingCooldowns[cooldownKey]
                            if lastGreeting then
                                local timeSinceLastGreeting = os.time() - lastGreeting
                                if timeSinceLastGreeting < GREETING_COOLDOWN then
                                    continue
                                end
                            end

                            -- Comment out NPC-NPC system messages
                            -- local systemMessage = string.format(
                            --     "[SYSTEM] Another NPC (%s) has entered your area. You can initiate a conversation if you'd like.",
                            --     npc2.displayName
                            -- )
                            -- npcManagerV3:handleNPCInteraction(npc1, mockParticipant, systemMessage)
                            
                            greetingCooldowns[cooldownKey] = os.time()
                        end
                    end
                end
            end
        end
    end
end

-- Add near the top with other functions
local function getRandomPosition(origin, radius)
    local angle = math.random() * math.pi * 2
    local distance = math.random() * radius
    return Vector3.new(
        origin.X + math.cos(angle) * distance,
        origin.Y,
        origin.Z + math.sin(angle) * distance
    )
end

local function moveNPC(npc, targetPosition)
    if not npc.model or not npc.model.PrimaryPart or not npc.model:FindFirstChild("Humanoid") then return end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    humanoid:MoveTo(targetPosition)
end

local function updateNPCMovement()
    while true do
        for _, npc in pairs(npcManagerV3.npcs) do
            -- Check if NPC can move and isn't busy
            local canMove = false
            for _, ability in ipairs(npc.abilities or {}) do
                if ability == "move" then
                    canMove = true
                    break
                end
            end

            if canMove and not npc.isInteracting then
                -- Random chance to start moving
                if math.random() < 0.8 then -- 80% chance each update
                    local spawnPos = npc.spawnPosition or npc.model.PrimaryPart.Position
                    local targetPos = getRandomPosition(spawnPos, 10) -- 10 stud radius
                    
                    LoggerService:debug("MOVEMENT", string.format(
                        "Moving %s to random position (%.1f, %.1f, %.1f)",
                        npc.displayName,
                        targetPos.X,
                        targetPos.Y,
                        targetPos.Z
                    ))
                    
                    moveNPC(npc, targetPos)
                end
            end
        end
        wait(5) -- Check every 5 seconds
    end
end

-- Modify the main update loop to remove the call
local function updateNPCs()
    LoggerService:info("SYSTEM", "Starting NPC update loop")
    spawn(updateNPCMovement) -- Start movement system in parallel
    
    while true do
        -- Calculate clusters first
        local clusters = interactionService:updateProximityMatrix()  -- Use instance
        LoggerService:debug("PROXIMITY", string.format("Got %d clusters from InteractionService", #clusters))
        
        -- Only proceed if we have valid clusters
        if clusters and #clusters > 0 then
            -- Use the fresh cluster data for all proximity checks
            checkPlayerProximity(clusters)
            checkNPCProximity(clusters)
        end
        
        wait(1)
    end
end

spawn(updateNPCs)

-- Handle player-initiated interaction ending
local EndInteractionEvent = Instance.new("RemoteEvent")
EndInteractionEvent.Name = "EndInteractionEvent"
EndInteractionEvent.Parent = ReplicatedStorage

EndInteractionEvent.OnServerEvent:Connect(function(player)
	local interactingNPC = interactionController:getInteractingNPC(player)
	if interactingNPC then
		LoggerService:info("INTERACTION", string.format("Player %s manually ended interaction with %s", 
			player.Name, interactingNPC.displayName))
		npcManagerV3:endInteraction(interactingNPC, player)
	end
end)

LoggerService:info("SYSTEM", "NPC system V3 main script running")

-- At the top with other requires
local NPCChatHandlerDep = ReplicatedStorage.Shared.NPCSystem:FindFirstChild("NPCChatHandler.dep")
if NPCChatHandlerDep then
    LoggerService:warn("SYSTEM", "Found deprecated NPCChatHandler.dep - this file should be removed")
    
    -- Try to load it to see if anything still depends on it
    local success, result = pcall(function()
        return require(NPCChatHandlerDep)
    end)
    
    if success then
        LoggerService:warn("SYSTEM", "NPCChatHandler.dep was loaded successfully - may still be in use")
    else
        LoggerService:info("SYSTEM", "NPCChatHandler.dep failed to load - safe to remove")
    end
end
