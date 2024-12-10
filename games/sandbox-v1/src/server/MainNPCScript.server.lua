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
local npcManagerV3 = NPCManagerV3.getInstance()
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

-- Add at the top with other state variables
local activeConversations = {
    playerToNPC = {}, -- player UserId -> npcId
    npcToNPC = {},    -- npc Id -> npc Id
    npcToPlayer = {}  -- npc Id -> player UserId
}

local function checkPlayerProximity()
    -- Only check every 5 seconds instead of 2
    wait(5)
    
    local players = Players:GetPlayers()
    for _, npc in pairs(npcManagerV3.npcs) do
        for _, player in ipairs(players) do
            local distance = calculateDistance(player, npc)
            if distance <= npc.responseRadius then
                -- Only log when entering/leaving range
                if not lastPlayerDistances[player.UserId .. npc.id] or 
                   (lastPlayerDistances[player.UserId .. npc.id] > npc.responseRadius) then
                    Logger:log("RANGE", string.format("Player %s entered range of %s", 
                        player.Name, npc.displayName))
                end
            end
            lastPlayerDistances[player.UserId .. npc.id] = distance
        end
    end
end

local function checkNPCProximity() 
    wait(5) -- Check every 5 seconds
    
    for _, npc1 in pairs(npcManagerV3.npcs) do
        for _, npc2 in pairs(npcManagerV3.npcs) do
            if npc1.id ~= npc2.id then
                local distance = calculateDistance(npc1, npc2)
                -- Only log when entering/leaving range
                if distance <= npc1.responseRadius then
                    if not lastNPCDistances[npc1.id .. npc2.id] or
                       (lastNPCDistances[npc1.id .. npc2.id] > npc1.responseRadius) then
                        Logger:log("RANGE", string.format("NPC %s entered range of %s",
                            npc1.displayName, npc2.displayName))
                    end
                end
                lastNPCDistances[npc1.id .. npc2.id] = distance
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
            Logger:log("RANGE", string.format(
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
                Logger:log("DEBUG", string.format(
                    "Skipping player greeting - on cooldown for %d more seconds",
                    GREETING_COOLDOWN - timeSinceLastGreeting
                ))
                return
            end
        end

        Logger:log("INTERACTION", string.format("Routing chat from %s to NPC %s (Distance: %.2f)", 
            player.Name, closestNPC.displayName, closestDistance))
        npcManagerV3:handleNPCInteraction(closestNPC, player, message)
        
        if isGreeting then
            greetingCooldowns[cooldownKey] = os.time()
        end
    else
        Logger:log("INTERACTION", string.format(
            "No NPCs in range for player %s chat", 
            player.Name
        ))
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

local function checkOngoingConversations()
    for npc1Id, conversationData in pairs(activeConversations.npcToNPC) do
        local npc1 = npcManagerV3.npcs[npc1Id]
        local npc2 = conversationData.partner
        
        if npc1 and npc2 and npc1.model and npc2.model then
            local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
            local isInRange = distance <= npc1.responseRadius
            
            Logger:log("RANGE", string.format(
                "[ONGOING] Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                npc1.displayName,
                npc2.displayName,
                distance,
                npc1.responseRadius,
                tostring(isInRange)
            ))

            if not isInRange then
                Logger:log("INTERACTION", string.format(
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
                    
                    Logger:log("MOVEMENT", string.format(
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
    Logger:log("SYSTEM", "Starting NPC update loop")
    spawn(updateNPCMovement) -- Start movement system in parallel
    while true do
        checkPlayerProximity()
        checkNPCProximity()
        checkOngoingConversations()
        wait(2) -- Increase wait time from 1 to 2 seconds
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
