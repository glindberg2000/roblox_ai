-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

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
local greetingCooldowns = {}
local GREETING_COOLDOWN = 30 -- seconds between greetings

-- Add at the top with other state variables
local activeConversations = {
    playerToNPC = {}, -- player UserId -> npcId
    npcToNPC = {},    -- npc Id -> npc Id
    npcToPlayer = {}  -- npc Id -> player UserId
}

local function checkPlayerProximity()
    for _, player in ipairs(Players:GetPlayers()) do
        local playerPosition = player.Character and player.Character.PrimaryPart
        if playerPosition then
            for _, npc in pairs(npcManagerV3.npcs) do
                if npc.model and npc.model.PrimaryPart then
                    local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
                    local isInRange = distance <= npc.responseRadius

                    -- Log range check for debugging
                    LoggerService:debug("RANGE", string.format(
                        "[PLAYER] Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                        player.Name,
                        npc.displayName,
                        distance,
                        npc.responseRadius,
                        tostring(isInRange)
                    ))

                    -- Only proceed if in range and NPC isn't busy
                    if isInRange and not npc.isInteracting and not activeConversations.npcToPlayer[npc.id] then
                        -- Check if NPC has initiate_chat ability
                        local hasInitiateAbility = false
                        for _, ability in ipairs(npc.abilities or {}) do
                            if ability == "initiate_chat" then
                                hasInitiateAbility = true
                                break
                            end
                        end

                        if hasInitiateAbility and interactionController:canInteract(player) then
                            -- Check cooldown
                            local cooldownKey = npc.id .. "_" .. player.UserId
                            local lastGreeting = greetingCooldowns[cooldownKey]
                            if lastGreeting then
                                local timeSinceLastGreeting = os.time() - lastGreeting
                                if timeSinceLastGreeting < GREETING_COOLDOWN then continue end
                            end

                            LoggerService:debug("DEBUG", string.format("NPC initiating chat: %s -> %s", 
                                npc.displayName, player.Name))

                            -- Lock conversation
                            activeConversations.npcToPlayer[npc.id] = player.UserId
                            activeConversations.playerToNPC[player.UserId] = npc.id

                            -- Send system message about player in range
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

    -- Find closest NPC in range
    local closestNPC, closestDistance = nil, math.huge

    for _, npc in pairs(npcManagerV3.npcs) do
        if npc.model and npc.model.PrimaryPart then
            local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
            
            -- Log range check for debugging
            LoggerService:debug("RANGE", string.format(
                "Distance between player %s and NPC %s: %.2f studs (Radius: %d, InRange: %s)",
                player.Name,
                npc.displayName,
                distance,
                npc.responseRadius,
                tostring(distance <= npc.responseRadius)
            ))

            -- Only consider NPCs in range and not already interacting
            if distance <= npc.responseRadius and distance < closestDistance and not npc.isInteracting then
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

local function checkNPCProximity()
    for _, npc1 in pairs(npcManagerV3.npcs) do
        -- Skip if no initiate_chat
        local hasInitiateAbility = false
        for _, ability in ipairs(npc1.abilities or {}) do
            if ability == "initiate_chat" then
                hasInitiateAbility = true
                break
            end
        end
        if not hasInitiateAbility then continue end

        -- Scan for other NPCs in range
        for _, npc2 in pairs(npcManagerV3.npcs) do
            if npc1 == npc2 or npc2.isInteracting then continue end
            if not npc2.model or not npc2.model.PrimaryPart then continue end

            local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
            local isInRange = distance <= npc1.responseRadius
            
            LoggerService:debug("RANGE", string.format(
                "Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                npc1.displayName,
                npc2.displayName,
                distance,
                npc1.responseRadius,
                tostring(isInRange)
            ))

            -- Only proceed if in range and not already in conversation
            if not isInRange then continue end
            if activeConversations.npcToNPC[npc1.id] then continue end
            if activeConversations.npcToNPC[npc2.id] then continue end

            -- Check cooldown
            local cooldownKey = npc1.id .. "_" .. npc2.id
            local lastGreeting = greetingCooldowns[cooldownKey]
            if lastGreeting then
                local timeSinceLastGreeting = os.time() - lastGreeting
                if timeSinceLastGreeting < GREETING_COOLDOWN then continue end
            end

            LoggerService:info("INTERACTION", string.format("%s sees %s and can initiate chat", 
                npc1.displayName, npc2.displayName))
            
            -- Lock conversation
            activeConversations.npcToNPC[npc1.id] = {partner = npc2}
            activeConversations.npcToNPC[npc2.id] = {partner = npc1}
            
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

local function checkOngoingConversations()
    for npc1Id, conversationData in pairs(activeConversations.npcToNPC) do
        local npc1 = npcManagerV3.npcs[npc1Id]
        local npc2 = conversationData.partner
        
        if npc1 and npc2 and npc1.model and npc2.model then
            local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
            local isInRange = distance <= npc1.responseRadius
            
            LoggerService:debug("RANGE", string.format(
                "[ONGOING] Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                npc1.displayName,
                npc2.displayName,
                distance,
                npc1.responseRadius,
                tostring(isInRange)
            ))

            if not isInRange then
                LoggerService:info("INTERACTION", string.format(
                    "Ending conversation - NPCs out of range (%s <-> %s)",
                    npc1.displayName,
                    npc2.displayName
                ))
                npcManagerV3:endInteraction(npc1, npc2)
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

            if canMove and not npc.isInteracting and 
               not activeConversations.npcToNPC[npc.id] and 
               not activeConversations.npcToPlayer[npc.id] then
                
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

-- Add to the main update loop
local function updateNPCs()
    LoggerService:info("SYSTEM", "Starting NPC update loop")
    spawn(updateNPCMovement) -- Start movement system in parallel
    while true do
        checkPlayerProximity()
        checkNPCProximity()
        checkOngoingConversations()
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
