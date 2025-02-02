-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)
local InteractionService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.InteractionService)

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
local greetingCooldowns = {} -- Track when NPCs last greeted each other

-- Add at the top with other state variables
-- local activeConversations = { ... }

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

                        -- Remove conversation locks
                        if npc and interactionController:canInteract(player) then
                            -- Only check cooldown
                            local cooldownKey = npc.id .. "_" .. player.UserId
                            local lastGreeting = greetingCooldowns[cooldownKey]
                            if lastGreeting then
                                local timeSinceLastGreeting = os.time() - lastGreeting
                                if timeSinceLastGreeting < GREETING_COOLDOWN then
                                    continue
                                end
                            end

                            local systemMessage = string.format(
                                "[SYSTEM] A player (%s) has entered your area. You can initiate a conversation if you'd like.",
                                player.Name
                            )
                            npcManagerV3:handleNPCInteraction(npc, player, systemMessage)
                            greetingCooldowns[cooldownKey] = os.time()
                        end
                    end
                end
            end
        end
    end
end

local function onPlayerChatted(player, message)
    -- Get player position
    local playerPosition = player.Character and player.Character.PrimaryPart
    if not playerPosition then return end

    -- Find closest NPC in range that's in same cluster
    local closestNPC, closestDistance = nil, math.huge

    for _, npc in pairs(npcManagerV3.npcs) do
        -- Use existing cluster check
        if not interactionService:canInteract(player, npc) then
            continue
        end

        if npc.model and npc.model.PrimaryPart then
            local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
            
            LoggerService:debug("RANGE", string.format(
                "Distance between player %s and NPC %s: %.2f studs (Radius: %d, InRange: %s)",
                player.Name,
                npc.displayName,
                distance,
                npc.responseRadius,
                tostring(distance <= npc.responseRadius)
            ))

            if distance <= npc.responseRadius and distance < closestDistance then
                closestNPC, closestDistance = npc, distance
            end
        end
    end

    if closestNPC then
        local cooldownKey = closestNPC.id .. "_" .. player.UserId
        local lastGreeting = greetingCooldowns[cooldownKey]
        local isGreeting = message:lower():match("^h[ae][yl]l?o+!?$") or message:lower() == "hi"
        
        if isGreeting and lastGreeting then
            local timeSinceLastGreeting = os.time() - lastGreeting
            if timeSinceLastGreeting < GREETING_COOLDOWN then
                LoggerService:debug("DEBUG", string.format(
                    "Skipping player greeting - on cooldown for %d more seconds",
                    GREETING_COOLDOWN - timeSinceLastGreeting
                ))
                return
            end
        end

        LoggerService:info("INTERACTION", string.format("Routing chat from %s to NPC %s (Distance: %.2f)", 
            player.Name, closestNPC.displayName, closestDistance))
        npcManagerV3:handleNPCInteraction(closestNPC, player, message)
        
        if isGreeting then
            greetingCooldowns[cooldownKey] = os.time()
        end
    else
        LoggerService:info("INTERACTION", string.format(
            "No NPCs in range for player %s chat", 
            player.Name
        ))
    end
end

local function setupChatConnections()
	LoggerService:info("SYSTEM", "Setting up chat connections")
	Players.PlayerAdded:Connect(function(player)
		LoggerService:info("STATE", string.format("Setting up chat connection for player: %s", player.Name))
		player.Chatted:Connect(function(message)
			onPlayerChatted(player, message)
		end)
	end)
end

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

                            -- Create mock participant and initiate
                            local mockParticipant = npcManagerV3:createMockParticipant(npc2)
                            local systemMessage = string.format(
                                "[SYSTEM] Another NPC (%s) has entered your area. You can initiate a conversation if you'd like.",
                                npc2.displayName
                            )
                            npcManagerV3:handleNPCInteraction(npc1, mockParticipant, systemMessage)
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

local function handleChatRequest(player)
    local playerPosition = player.Character and player.Character.PrimaryPart
    if not playerPosition then return end

    -- Use existing cluster system
    local clusters = InteractionService:getLatestClusters()
    local playerCluster = nil
    
    -- Find which cluster the player is in
    for _, cluster in ipairs(clusters) do
        if table.find(cluster.members, player.Name) then
            playerCluster = cluster
            break
        end
    end

    -- If player isn't in a cluster, they can't interact
    if not playerCluster then return end

    -- Find closest NPC that's in the same cluster
    local closestNPC, closestDistance = nil, math.huge
    for _, npc in pairs(npcManagerV3.npcs) do
        if npc.model and npc.model.PrimaryPart then
            -- Check if NPC is in same cluster as player
            if table.find(playerCluster.members, npc.displayName) then
                local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
                if distance < closestDistance and not npc.isInteracting then
                    closestNPC, closestDistance = npc, distance
                end
            end
        end
    end

    return closestNPC, closestDistance
end
