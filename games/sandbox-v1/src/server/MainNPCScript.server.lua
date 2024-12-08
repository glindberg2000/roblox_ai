-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local Logger = require(ServerScriptService:WaitForChild("Logger"))

local success, result = pcall(function()
	return require(ServerScriptService:WaitForChild("InteractionController", 5))
end)

if success then
	InteractionController = result
	Logger:log("SYSTEM", "InteractionController loaded successfully")
else
	Logger:log("ERROR", "Failed to load InteractionController: " .. tostring(result))
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

local Logger = require(ServerScriptService:WaitForChild("Logger"))

-- Move ensureStorage to the top, before NPC initialization
local function ensureStorage()
    local ServerStorage = game:GetService("ServerStorage")
    
    -- Create Assets/npcs folder structure
    local Assets = ServerStorage:FindFirstChild("Assets") or 
                   Instance.new("Folder", ServerStorage)
    Assets.Name = "Assets"
    
    local npcs = Assets:FindFirstChild("npcs") or 
                 Instance.new("Folder", Assets)
    npcs.Name = "npcs"
    
    Logger:log("SYSTEM", "Storage structure verified")
end

-- Call ensureStorage first
ensureStorage()

-- Then initialize NPC system
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))
Logger:log("SYSTEM", "Starting NPC initialization")
local npcManagerV3 = NPCManagerV3.new()
Logger:log("SYSTEM", "NPC Manager created")

-- Debug NPC abilities
for npcId, npcData in pairs(npcManagerV3.npcs) do
	Logger:log("DEBUG", string.format("NPC %s abilities: %s", 
		npcData.displayName,
		table.concat(npcData.abilities or {}, ", ")
	))
end

for npcId, npcData in pairs(npcManagerV3.npcs) do
	Logger:log("STATE", string.format("NPC spawned: %s", npcData.displayName))
end

local interactionController = npcManagerV3.interactionController

Logger:log("SYSTEM", "NPC system V3 initialized")

-- Add cooldown tracking
local greetingCooldowns = {}
local GREETING_COOLDOWN = 30 -- seconds between greetings

local function checkPlayerProximity()
	for _, player in ipairs(Players:GetPlayers()) do
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if playerPosition then
			for _, npc in pairs(npcManagerV3.npcs) do
				if npc.model and npc.model.PrimaryPart then
					local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
					-- Only greet if player just entered range
					local wasInRange = npc.playersInRange and npc.playersInRange[player.UserId]
					local isInRange = distance <= npc.responseRadius
					
					-- Track players in range
					npc.playersInRange = npc.playersInRange or {}
					npc.playersInRange[player.UserId] = isInRange
					
					-- Only initiate if player just entered range and NPC isn't busy
					if isInRange and not wasInRange and not npc.isInteracting then
						-- Check cooldown first
						local cooldownKey = npc.id .. "_" .. player.UserId
						local lastGreeting = greetingCooldowns[cooldownKey]
						if lastGreeting then
							local timeSinceLastGreeting = os.time() - lastGreeting
							if timeSinceLastGreeting < GREETING_COOLDOWN then
								Logger:log("DEBUG", string.format(
									"Skipping greeting - on cooldown for %d more seconds",
									GREETING_COOLDOWN - timeSinceLastGreeting
								))
								continue
							end
						end

						-- Check if NPC has initiate_chat ability
						local hasInitiateAbility = false
						if npc.abilities then
							for _, ability in ipairs(npc.abilities) do
								if ability == "initiate_chat" then
									hasInitiateAbility = true
									break
								end
							end
						end

						if hasInitiateAbility and interactionController:canInteract(player) then
							Logger:log("DEBUG", string.format("Attempting to initiate chat: %s -> %s", 
								npc.displayName, player.Name))
							-- Send system message about player entering range
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
	Logger:log("INTERACTION", string.format("Player %s chatted: %s", player.Name, message))
	
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not playerPosition then
		Logger:log("ERROR", string.format("Cannot process chat for %s: Character not found", player.Name))
		return
	end

	local closestNPC, closestDistance = nil, math.huge

	for _, npc in pairs(npcManagerV3.npcs) do
		if npc.model and npc.model.PrimaryPart then
			local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
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
				Logger:log("DEBUG", string.format(
					"Skipping player greeting - on cooldown for %d more seconds",
					GREETING_COOLDOWN - timeSinceLastGreeting
				))
				return
			end
		end

		Logger:log("INTERACTION", string.format("Routing chat from %s to NPC %s", 
			player.Name, closestNPC.displayName))
		npcManagerV3:handleNPCInteraction(closestNPC, player, message)
		
		if isGreeting then
			greetingCooldowns[cooldownKey] = os.time()
		end
	end
end

local function setupChatConnections()
	Logger:log("SYSTEM", "Setting up chat connections")
	Players.PlayerAdded:Connect(function(player)
		Logger:log("STATE", string.format("Setting up chat connection for player: %s", player.Name))
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

        -- Skip if already interacting
        if npc1.isInteracting then continue end

        -- Skip if reached max concurrent chats
        local activeChats = 0
        for _, thread in pairs(npcManagerV3.threadPool.interactionThreads or {}) do
            if thread.npc == npc1 then
                activeChats = activeChats + 1
            end
        end
        if activeChats >= 1 then continue end

        -- Scan for other NPCs in range
        for _, npc2 in pairs(npcManagerV3.npcs) do
            if npc1 == npc2 or npc2.isInteracting then continue end
            if not npc2.model or not npc2.model.PrimaryPart then continue end

            local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
            
            -- Check if they just came into range
            local wasInRange = npc1.npcsInRange and npc1.npcsInRange[npc2.id]
            local isInRange = distance <= npc1.responseRadius

            -- Track NPCs in range
            npc1.npcsInRange = npc1.npcsInRange or {}
            npc1.npcsInRange[npc2.id] = isInRange

            if isInRange and not wasInRange then
                -- Check cooldown
                local cooldownKey = npc1.id .. "_" .. npc2.id
                local lastGreeting = greetingCooldowns[cooldownKey]
                if lastGreeting then
                    local timeSinceLastGreeting = os.time() - lastGreeting
                    if timeSinceLastGreeting < GREETING_COOLDOWN then continue end
                end

                -- Also check reverse cooldown
                local reverseCooldownKey = npc2.id .. "_" .. npc1.id
                local reverseLastGreeting = greetingCooldowns[reverseCooldownKey]
                if reverseLastGreeting then
                    local reverseTimeSinceLastGreeting = os.time() - reverseLastGreeting
                    if reverseTimeSinceLastGreeting < GREETING_COOLDOWN then continue end
                end

                Logger:log("INTERACTION", string.format("%s sees %s and can initiate chat", 
                    npc1.displayName, npc2.displayName))
                
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

local function updateNPCs()
    Logger:log("SYSTEM", "Starting NPC update loop")
    while true do
        checkPlayerProximity()
        checkNPCProximity()
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
		Logger:log("INTERACTION", string.format("Player %s manually ended interaction with %s", 
			player.Name, interactingNPC.displayName))
		npcManagerV3:endInteraction(interactingNPC, player)
	end
end)

Logger:log("SYSTEM", "NPC system V3 main script running")
