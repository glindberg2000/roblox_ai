# sandbox-v1 Documentation

Generated: 2024-12-20 01:45:46

## Directory Structure

```
├── assets
│   ├── clothings
│   ├── npcs
│   ├── props
│   └── test1
├── client
│   ├── NPCClientChatHandler.lua
│   └── NPCClientHandler.client.lua
├── data
│   ├── AssetDatabase.lua
│   ├── NPCDatabase.lua
│   └── PlayerDatabase.json
├── server
│   ├── AssetInitializer.server.lua
│   ├── ChatSetup.server.lua
│   ├── InteractionController.lua
│   ├── MainNPCScript.server.lua
│   ├── MockPlayerTest.server.lua
│   ├── NPCInteractionTest.server.lua
│   ├── NPCSystemInitializer.server.lua
│   ├── PlayerJoinHandler.server.lua
│   └── test.server.lua
├── shared
│   ├── NPCSystem
│   │   ├── actions
│   │   │   └── ActionRouter.lua
│   │   ├── chat
│   │   │   ├── ChatUtils.lua
│   │   │   ├── NPCChatHandler.lua
│   │   │   ├── V3ChatClient.lua
│   │   │   └── V4ChatClient.lua
│   │   ├── config
│   │   │   ├── InteractionConfig.lua
│   │   │   ├── LettaConfig.lua
│   │   │   ├── NPCConfig.lua
│   │   │   └── PerformanceConfig.lua
│   │   ├── services
│   │   │   ├── ActionService.lua
│   │   │   ├── AnimationService.lua
│   │   │   ├── InteractionService.lua
│   │   │   ├── LoggerService.lua
│   │   │   ├── ModelLoader.lua
│   │   │   ├── MovementService.lua
│   │   │   └── VisionService.lua
│   │   ├── NPCDatabase.lua
│   │   ├── NPCManagerV3.lua
│   │   └── config.lua
│   ├── AssetModule.lua
│   ├── ChatRouter.lua
│   ├── ConversationManager.lua
│   ├── ConversationManagerV2.lua
│   ├── PerformanceMonitor.lua
│   ├── VisionConfig.lua
│   └── test.lua
└── test
    └── NPCInteractionTest.lua
```

## Source Files

### test/NPCInteractionTest.lua

```lua
function runNPCInteractionTests()
    -- ... existing setup ...

    -- Test 1: Basic NPC-to-NPC interaction
    print("Test 1: Initiating basic NPC-to-NPC interaction")
    local mockParticipant = npcManager:createMockParticipant(npc1)
    
    -- Verify mock participant
    assert(mockParticipant.Type == "npc", "Mock participant should be of type 'npc'")
    assert(mockParticipant.model == npc1.model, "Mock participant should have correct model reference")
    assert(mockParticipant.npcId == npc1.id, "Mock participant should have correct NPC ID")
    
    -- Start interaction
    local success, err = pcall(function()
        npcManager:handleNPCInteraction(npc2, mockParticipant, "Hello!")
        wait(2) -- Wait for the interaction to process
        
        -- Verify states
        assert(npc2.isInteracting, "NPC2 should be in interaction state")
        assert(npc2.model.Humanoid.WalkSpeed == 0, "NPC2 should be locked in place")
        
        -- Check for response
        assert(#npc2.chatHistory > 0, "NPC2 should have responded")
        print("NPC2 response: " .. npc2.chatHistory[#npc2.chatHistory])
    end)
    
    if not success then
        error("Interaction test failed: " .. tostring(err))
    end
    
    -- Clean up
    npcManager:endInteraction(npc2, mockParticipant)
    wait(1)
    
    -- Verify cleanup
    assert(not npc2.isInteracting, "NPC2 should not be in interaction state")
    assert(npc2.model.Humanoid.WalkSpeed > 0, "NPC2 should be unlocked")

    print("All NPC-to-NPC interaction tests passed!")
end 
```

### server/PlayerJoinHandler.server.lua

```lua
--PlayerJoinHandler.server.lua
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")

-- Initialize Logger
local Logger = require(NPCSystem.services.LoggerService)

-- Folder to store player descriptions in ReplicatedStorage
local PlayerDescriptionsFolder = ReplicatedStorage:FindFirstChild("PlayerDescriptions")
	or Instance.new("Folder", ReplicatedStorage)
PlayerDescriptionsFolder.Name = "PlayerDescriptions"

local API_URL = "https://roblox.ella-ai-care.com/get_player_description"

-- Function to send player ID to an external API and get a description
local function getPlayerDescriptionFromAPI(userId)
	local data = { user_id = tostring(userId) }

	-- API call to get the player description
	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson)
	end)

	if success then
		local parsedResponse = HttpService:JSONDecode(response)

		-- Check if the API response contains a valid description
		if parsedResponse and parsedResponse.description then
			Logger:log("API", string.format("Received response from API for userId: %s", userId))
			return parsedResponse.description
		else
			Logger:log("ERROR", string.format("API response missing 'description' for userId: %s", userId))
			return "No description available"
		end
	else
		Logger:log("ERROR", string.format("Failed to get player description from API for userId: %s. Error: %s", 
            userId, 
            tostring(response)
        ))
		return "Error retrieving description"
	end
end

-- Function to store player description in ReplicatedStorage
local function storePlayerDescription(playerName, description)
	-- Create or update the player's description in ReplicatedStorage
	local existingDesc = PlayerDescriptionsFolder:FindFirstChild(playerName)
	if existingDesc then
		existingDesc.Value = description
		Logger:log("DATABASE", string.format("Updated description for player: %s", playerName))
	else
		local playerDesc = Instance.new("StringValue")
		playerDesc.Name = playerName
		playerDesc.Value = description
		playerDesc.Parent = PlayerDescriptionsFolder
		Logger:log("DATABASE", string.format("Created new description for player: %s", playerName))
	end
end

-- Event handler for when a player joins the game
local function onPlayerAdded(player)
	Logger:log("INTERACTION", string.format("Player joined: %s (UserId: %s)", 
        player.Name, 
        player.UserId
    ))

	-- Get the player's description from the API
	local description = getPlayerDescriptionFromAPI(player.UserId)

	-- Store the description in ReplicatedStorage
	if description then
		storePlayerDescription(player.Name, description)
		Logger:log("STATE", string.format("Stored description for player: %s -> %s", 
            player.Name, 
            description
        ))
	else
		local fallbackDescription = "A player named " .. player.Name
		storePlayerDescription(player.Name, fallbackDescription)
		Logger:log("WARN", string.format("Using fallback description for player: %s -> %s", 
            player.Name, 
            fallbackDescription
        ))
	end
end

-- Connect the PlayerAdded event to the onPlayerAdded function
Players.PlayerAdded:Connect(onPlayerAdded)

-- Ensure logs are displayed at server startup
Logger:log("SYSTEM", "PlayerJoinHandler initialized and waiting for players.")

```

### server/MainNPCScript.server.lua

```lua
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

```

### server/NPCSystemInitializer.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ServerScriptService = game:GetService("ServerScriptService")

print("NPCSystemInitializer: Starting initialization...")

-- Check if already initialized
if _G.NPCSystemInitialized then
	print("NPCSystemInitializer: System already initialized, skipping...")
	return
end

-- Set initialization flag at the very start
_G.NPCSystemInitialized = true

-- Wait for critical paths
local Shared = ReplicatedStorage:WaitForChild("Shared", 10)
if not Shared then
	print("Failed to find Shared folder")
	return
end

local NPCSystem = Shared:WaitForChild("NPCSystem", 10)
if not NPCSystem then
	print("Failed to find NPCSystem folder")
	return
end

print("Found NPCSystem")
print("Path: " .. tostring(NPCSystem:GetFullName()))
print("NPCSystem children:")
for _, child in ipairs(NPCSystem:GetChildren()) do
	print("Child: " .. tostring(child.Name) .. " (" .. tostring(child.ClassName) .. ")")
end

-- Try to load Logger first
print("NPCSystemInitializer: Attempting to load LoggerService...")

local services = NPCSystem:WaitForChild("services")
if not services then
	print("Failed to find services folder")
	return
end

local LoggerService = services:WaitForChild("LoggerService")
if not LoggerService then
	print("Failed to find LoggerService")
	return
end

local success, Logger = pcall(function()
	return require(LoggerService)
end)

if not success then
	print("Failed to load LoggerService - error: " .. tostring(Logger))
	return
end

print("NPCSystemInitializer: LoggerService loaded")

local function ensureStorage()
	print("NPCSystemInitializer: Verifying storage folders...")

	-- Only dynamically create Workspace folders
	local NPCsFolder = workspace:FindFirstChild("NPCs")
	if not NPCsFolder then
		NPCsFolder = Instance.new("Folder")
		NPCsFolder.Name = "NPCs"
		NPCsFolder.Parent = workspace
		print("Created 'NPCs' folder in workspace.")
	end

	print("NPCSystemInitializer: Storage verification complete.")
end

local npcsFolder = ensureStorage()

-- Initialize events for NPC chat and interaction
if not ReplicatedStorage:FindFirstChild("NPCChatEvent") then
	local NPCChatEvent = Instance.new("RemoteEvent")
	NPCChatEvent.Name = "NPCChatEvent"
	NPCChatEvent.Parent = ReplicatedStorage
	print("Created NPCChatEvent")
end

if not ReplicatedStorage:FindFirstChild("EndInteractionEvent") then
	local EndInteractionEvent = Instance.new("RemoteEvent")
	EndInteractionEvent.Name = "EndInteractionEvent"
	EndInteractionEvent.Parent = ReplicatedStorage
	print("Created EndInteractionEvent")
end

print("NPCSystemInitializer: Events created")

-- Try to load NPCManagerV3
print("NPCSystemInitializer: Attempting to load NPCManagerV3...")
print("NPCManagerV3 path: " .. tostring(NPCSystem.NPCManagerV3:GetFullName()))

local success, NPCManagerV3 = pcall(function()
	return require(NPCSystem.NPCManagerV3)
end)

if not success then
	print("Failed to load NPCManagerV3: " .. tostring(NPCManagerV3))
	return
end

print("NPCSystemInitializer: NPCManagerV3 loaded")

-- Create and store NPCManager instance
local npcManager = NPCManagerV3.getInstance()
if not npcManager then
	print("Failed to get NPCManagerV3 instance")
	return
end

_G.NPCManager = npcManager

print("NPCSystemInitializer: Initialization complete")

```

### server/ChatSetup.server.lua

```lua
local ChatService = game:GetService("Chat")
local ServerScriptService = game:GetService("ServerScriptService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

LoggerService:info("SYSTEM", "Setting up chat service")

-- Enable bubble chat without using deprecated method
ChatService.BubbleChatEnabled = true

LoggerService:info("SYSTEM", "Chat setup completed")
```

### server/test.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function testSync()
    print("Testing sync...")
    
    -- Test Shared folder
    local shared = ReplicatedStorage:WaitForChild("Shared", 5)
    if shared then
        print("Found Shared folder")
        
        -- Test NPCSystem folder
        local npcSystem = shared:WaitForChild("NPCSystem", 5)
        if npcSystem then
            print("Found NPCSystem folder")
            
            -- Test services folder
            local services = npcSystem:WaitForChild("services", 5)
            if services then
                print("Found services folder")
                
                -- Try to load LoggerService
                local success, result = pcall(function()
                    return require(services.LoggerService)
                end)
                if success then
                    print("Successfully loaded LoggerService")
                else
                    warn("Failed to load LoggerService:", result)
                end
            end
        end
    end
end

testSync() 
```

### server/AssetInitializer.server.lua

```lua
-- AssetInitializer.server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Load the AssetDatabase file directly
local AssetDatabase = require(game:GetService("ServerScriptService").AssetDatabase)

-- Ensure LocalDB folder exists (managed by Rojo)
local LocalDB = ReplicatedStorage:FindFirstChild("LocalDB")
if not LocalDB or not LocalDB:IsA("Folder") then
    error("LocalDB folder not found in ReplicatedStorage! Check Rojo sync.")
end

-- Create a lookup table for assets by name
local AssetLookup = {}

-- Function to store asset descriptions in ReplicatedStorage
-- Function to store asset descriptions in ReplicatedStorage
local function storeAssetDescriptions(assetId, name, description, imageUrl)
    local assetEntry = LocalDB:FindFirstChild(assetId)
    if assetEntry then
        assetEntry:Destroy() -- Remove existing entry to ensure we're updating all fields
    end

    assetEntry = Instance.new("Folder")
    assetEntry.Name = assetId
    assetEntry.Parent = LocalDB

    -- Create and set name value with fallback
    local nameValue = Instance.new("StringValue")
    nameValue.Name = "Name"
    nameValue.Value = name or "Unknown Asset"
    nameValue.Parent = assetEntry

    -- Create and set description value with fallback
    local descValue = Instance.new("StringValue")
    descValue.Name = "Description"
    descValue.Value = description or "No description available"
    descValue.Parent = assetEntry

    -- Create and set image value with fallback
    local imageValue = Instance.new("StringValue")
    imageValue.Name = "ImageUrl"
    imageValue.Value = imageUrl or ""
    imageValue.Parent = assetEntry

    LoggerService:info("ASSET", string.format(
        "Stored asset: ID: %s, Name: %s, Description: %s",
        assetId,
        nameValue.Value,
        string.sub(descValue.Value, 1, 50) .. "..."
    ))
end

-- Initialize all assets from the local AssetDatabase
local function initializeAssets()
	for _, assetData in ipairs(AssetDatabase.assets) do
		storeAssetDescriptions(assetData.assetId, assetData.name, assetData.description, assetData.imageUrl)
	end
end

initializeAssets()
LoggerService:info("ASSET", "All assets initialized from local database")

-- Print out all stored assets for verification
LoggerService:info("ASSET", "Verifying stored assets in LocalDB:")
for _, assetEntry in ipairs(LocalDB:GetChildren()) do
	local nameValue = assetEntry:FindFirstChild("Name")
	local descValue = assetEntry:FindFirstChild("Description")
	local imageValue = assetEntry:FindFirstChild("ImageUrl")

	if nameValue and descValue and imageValue then
		LoggerService:info("ASSET", string.format(
			"Verified asset: ID: %s, Name: %s, Description: %s",
			assetEntry.Name,
			nameValue.Value,
			string.sub(descValue.Value, 1, 50) .. "..."
		))
	else
		LoggerService:warn("ASSET", string.format(
			"Error verifying asset: ID: %s, Name exists: %s, Description exists: %s, ImageUrl exists: %s",
			assetEntry.Name,
			tostring(nameValue ~= nil),
			tostring(descValue ~= nil),
			tostring(imageValue ~= nil)
		))
	end
end

-- Function to check a specific asset by name
local function checkAssetByName(assetName)
	local assetId = AssetLookup[assetName]
	if not assetId then
		LoggerService:warn("ASSET", string.format("Asset not found in lookup table: %s", assetName))
		return
	end
	
	local assetEntry = LocalDB:FindFirstChild(assetId)
	if not assetEntry then
		LoggerService:warn("ASSET", string.format("Asset entry not found for name: %s", assetName))
		return
	end
	
	local nameValue = assetEntry:FindFirstChild("Name")
	local descValue = assetEntry:FindFirstChild("Description")
	local imageValue = assetEntry:FindFirstChild("ImageUrl")

	LoggerService:debug("ASSET", string.format("Asset check by name: %s", assetName))
	LoggerService:debug("ASSET", string.format("  ID: %s", assetId))
	LoggerService:debug("ASSET", string.format("  Name exists: %s", tostring(nameValue ~= nil)))
	LoggerService:debug("ASSET", string.format("  Description exists: %s", tostring(descValue ~= nil)))
	LoggerService:debug("ASSET", string.format("  ImageUrl exists: %s", tostring(imageValue ~= nil)))

	if nameValue then
		LoggerService:debug("ASSET", string.format("  Name value: %s", nameValue.Value))
	end
	if descValue then
		LoggerService:debug("ASSET", string.format("  Description value: %s", string.sub(descValue.Value, 1, 50) .. "..."))
	end
	if imageValue then
		LoggerService:debug("ASSET", string.format("  ImageUrl value: %s", imageValue.Value))
	end
end

-- Check specific assets by name
checkAssetByName("sportymerch")
checkAssetByName("kid")

LoggerService:info("ASSET", "Asset initialization complete. AssetModule is now available in ReplicatedStorage")

-- Example of creating a new asset entry
local function createAssetEntry(assetId)
    local assetEntry = LocalDB:FindFirstChild(assetId)
    if not assetEntry then
        assetEntry = Instance.new("Folder")
        assetEntry.Name = assetId
        assetEntry.Parent = LocalDB
    end
    return assetEntry
end

```

### server/InteractionController.lua

```lua
-- ServerScriptService/InteractionController.lua
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Wait for critical paths
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local services = NPCSystem:WaitForChild("services")

local LoggerService = require(services.LoggerService)
local InteractionService = require(services.InteractionService)

local InteractionController = {}
InteractionController.__index = InteractionController

function InteractionController.new()
    local self = setmetatable({}, InteractionController)
    self.activeInteractions = {}
    LoggerService:log("SYSTEM", "InteractionController initialized")
    return self
end

function InteractionController:startInteraction(player, npc)
    if self.activeInteractions[player] then
        LoggerService:log("PLAYER", string.format("Player %s already in interaction", player.Name))
        return false
    end
    self.activeInteractions[player] = {npc = npc, startTime = tick()}
    LoggerService:log("PLAYER", string.format("Started interaction: %s with %s", player.Name, npc.displayName))
    return true
end

function InteractionController:endInteraction(player)
    LoggerService:log("PLAYER", string.format("Ending interaction for player %s", player.Name))
    self.activeInteractions[player] = nil
end

function InteractionController:canInteract(player)
    return not self.activeInteractions[player]
end

function InteractionController:getInteractingNPC(player)
    local interaction = self.activeInteractions[player]
    return interaction and interaction.npc or nil
end

function InteractionController:getInteractionState(player)
    local interaction = self.activeInteractions[player]
    if interaction then
        return {
            npc_id = interaction.npc.id,
            npc_name = interaction.npc.displayName,
            start_time = interaction.startTime,
            duration = tick() - interaction.startTime,
        }
    end
    return nil
end

function InteractionController:startGroupInteraction(players, npc)
    for _, player in ipairs(players) do
        self.activeInteractions[player] = {npc = npc, group = players, startTime = tick()}
    end
    LoggerService:log("PLAYER", string.format("Started group interaction with %d players", #players))
end

function InteractionController:isInGroupInteraction(player)
    local interaction = self.activeInteractions[player]
    return interaction and interaction.group ~= nil
end

function InteractionController:getGroupParticipants(player)
    local interaction = self.activeInteractions[player]
    if interaction and interaction.group then
        return interaction.group
    end
    return {player}
end

return InteractionController
```

### server/MockPlayerTest.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local MockPlayer = require(script.Parent.MockPlayer)
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Test function to run all checks
local function runTests()
    LoggerService:info("TEST", "Starting MockPlayer tests...")
    
    -- Test 1: Basic instantiation with type
    local testPlayer = MockPlayer.new("TestUser", 12345, "npc")
    assert(testPlayer ~= nil, "MockPlayer should be created successfully")
    assert(testPlayer.Name == "TestUser", "Name should match constructor argument")
    assert(testPlayer.DisplayName == "TestUser", "DisplayName should match Name")
    assert(testPlayer.UserId == 12345, "UserId should match constructor argument")
    assert(testPlayer.Type == "npc", "Type should be set to npc")
    LoggerService:info("TEST", "✓ Basic instantiation tests passed")
    
    -- Test 2: Default type behavior
    local defaultPlayer = MockPlayer.new("DefaultUser")
    assert(defaultPlayer.Type == "npc", "Default Type should be 'npc'")
    LoggerService:info("TEST", "✓ Default type test passed")
    
    -- Test 3: IsA functionality
    assert(testPlayer:IsA("Player") == true, "IsA('Player') should return true")
    LoggerService:info("TEST", "✓ IsA tests passed")
    
    -- Test 4: GetParticipantType functionality
    assert(testPlayer:GetParticipantType() == "npc", "GetParticipantType should return 'npc'")
    local playerTypeMock = MockPlayer.new("PlayerTest", 789, "player")
    assert(playerTypeMock:GetParticipantType() == "player", "GetParticipantType should return 'player'")
    LoggerService:info("TEST", "✓ GetParticipantType tests passed")
    
    LoggerService:info("TEST", "All MockPlayer tests passed successfully!")
end

-- Run tests in protected call to catch any errors
local success, error = pcall(runTests)
if not success then
    LoggerService:error("TEST", string.format("MockPlayer tests failed: %s", tostring(error)))
end 
```

### server/NPCInteractionTest.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local NPCManagerV3 = require(NPCSystem.NPCManagerV3)
local Logger = require(NPCSystem.services.LoggerService)

local function runNPCInteractionTests()
    print("Starting NPC-to-NPC interaction tests...")
    
    -- Get the singleton instance
    local npcManager = NPCManagerV3.new()
    
    -- Wait longer for NPCs to load from main initialization
    wait(5)
    
    -- Get two NPCs from the manager
    local npc1, npc2
    local npcCount = 0
    for id, npc in pairs(npcManager.npcs) do
        npcCount = npcCount + 1
        if npcCount == 1 then
            npc1 = npc
        elseif npcCount == 2 then
            npc2 = npc
            break
        end
    end
    
    if not (npc1 and npc2) then
        warn("Failed to find two NPCs for testing")
        return
    end
    
    -- Disable movement for both NPCs during test
    npc1.isMoving = false
    npc2.isMoving = false
    
    print(string.format("Testing interaction between %s and %s", npc1.displayName, npc2.displayName))
    
    -- Test 1: Basic NPC-to-NPC interaction
    print("Test 1: Initiating basic NPC-to-NPC interaction")
    local mockParticipant = npcManager:createMockParticipant(npc1)
    
    -- Verify mock participant
    assert(mockParticipant.Type == "npc", "Mock participant should be of type 'npc'")
    assert(mockParticipant.model == npc1.model, "Mock participant should have correct model reference")
    
    -- Start interaction
    local success, err = pcall(function()
        npcManager:handleNPCInteraction(npc2, mockParticipant, "Hello!")
        wait(1) -- Wait for interaction to process
        
        -- Verify interaction states
        assert(npc2.isInteracting, "NPC2 should be in interaction state")
        assert(not npc2.isMoving, "NPC2 should not be moving during interaction")
    end)
    
    if not success then
        error("Interaction test failed: " .. tostring(err))
    end
    
    print("✓ Basic interaction test passed")
    
    -- Clean up
    npcManager:endInteraction(npc2, mockParticipant)
    wait(1)
    
    -- Re-enable movement
    npc1.isMoving = true
    npc2.isMoving = true
    
    -- Test 1: Basic NPC-to-NPC interaction with movement locking
    print("Test 1: Testing NPC-to-NPC interaction with movement locking")
    local mockParticipant = npcManager:createMockParticipant(npc1)
    
    -- Start interaction
    local success, err = pcall(function()
        -- Verify initial states
        assert(npc1.isMoving == true, "NPC1 should be able to move initially")
        assert(npc2.isMoving == true, "NPC2 should be able to move initially")
        
        npcManager:handleNPCInteraction(npc2, mockParticipant, "Hello!")
        wait(1)
        
        -- Verify interaction states
        assert(npc2.isInteracting == true, "NPC2 should be in interaction state")
        assert(npc2.isMoving == false, "NPC2 should not be moving during interaction")
        assert(npc2.model.Humanoid.WalkSpeed == 0, "NPC2 walk speed should be 0")
        
        -- Get original NPC1 and verify its state
        local originalNPC1 = npcManager.npcs[tonumber(mockParticipant.UserId)]
        assert(originalNPC1.isMoving == false, "Original NPC1 should not be moving")
    end)
    
    if not success then
        error("Movement locking test failed: " .. tostring(err))
    end
    
    -- Test cleanup
    npcManager:endInteraction(npc2, mockParticipant)
    wait(1)
    
    -- Verify cleanup
    assert(npc2.isInteracting == false, "NPC2 should not be in interaction state after cleanup")
    assert(npc2.isMoving == true, "NPC2 should be able to move after cleanup")
    assert(npc2.model.Humanoid.WalkSpeed > 0, "NPC2 walk speed should be restored")
    
    print("All NPC interaction tests completed successfully!")
end

-- Run the tests in protected call
local success, error = pcall(function()
    runNPCInteractionTests()
end)

if not success then
    warn("NPC interaction tests failed: " .. tostring(error))
end 
```

### shared/ChatRouter.lua

```lua
local ChatRouter = {}

function ChatRouter.new()
    local self = setmetatable({}, {__index = ChatRouter})
    self.activeConversations = {
        playerToNPC = {}, -- player UserId -> NPC reference
        npcToPlayer = {}, -- NPC id -> player reference
        npcToNPC = {}     -- NPC id -> NPC reference
    }
    return self
end

function ChatRouter:isInConversation(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return self.activeConversations.playerToNPC[participant.UserId] ~= nil
    else
        return self.activeConversations.npcToPlayer[participant.npcId] ~= nil or 
               self.activeConversations.npcToNPC[participant.npcId] ~= nil
    end
end

function ChatRouter:getCurrentPartner(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return self.activeConversations.playerToNPC[participant.UserId]
    else
        return self.activeConversations.npcToPlayer[participant.npcId] or
               self.activeConversations.npcToNPC[participant.npcId]
    end
end

function ChatRouter:lockConversation(participant1, participant2)
    if typeof(participant1) == "Instance" and participant1:IsA("Player") then
        self.activeConversations.playerToNPC[participant1.UserId] = participant2
        self.activeConversations.npcToPlayer[participant2.npcId] = participant1
    else
        self.activeConversations.npcToNPC[participant1.npcId] = participant2
        self.activeConversations.npcToNPC[participant2.npcId] = participant1
    end
end

function ChatRouter:unlockConversation(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        local npc = self.activeConversations.playerToNPC[participant.UserId]
        if npc then
            self.activeConversations.playerToNPC[participant.UserId] = nil
            self.activeConversations.npcToPlayer[npc.npcId] = nil
        end
    else
        local partner = self.activeConversations.npcToNPC[participant.npcId]
        if partner then
            self.activeConversations.npcToNPC[participant.npcId] = nil
            self.activeConversations.npcToNPC[partner.npcId] = nil
        end
    end
end

function ChatRouter:routeMessage(message, sender, intendedReceiver)
    -- Get current conversation partner if any
    local currentPartner = self:getCurrentPartner(sender)
    
    -- If in conversation, force route to current partner
    if currentPartner then
        return currentPartner
    end
    
    -- If not in conversation and both participants are free, lock them
    if not self:isInConversation(sender) and not self:isInConversation(intendedReceiver) then
        self:lockConversation(sender, intendedReceiver)
        return intendedReceiver
    end
    
    return nil -- Cannot route message
end

return ChatRouter 
```

### shared/test.lua

```lua
return {
    test = function()
        print("Test module loaded!")
        return true
    end
} 
```

### shared/AssetModule.lua

```lua
-- src/shared/AssetModule.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LocalDB = ReplicatedStorage:WaitForChild("LocalDB")

local AssetModule = {}

function AssetModule.GetAssetDataByName(assetName)
	for _, assetEntry in ipairs(LocalDB:GetChildren()) do
		local nameValue = assetEntry:FindFirstChild("Name")
		if nameValue and nameValue.Value == assetName then
			local descValue = assetEntry:FindFirstChild("Description")
			local imageValue = assetEntry:FindFirstChild("ImageUrl")
			if descValue and imageValue then
				return {
					id = assetEntry.Name,
					name = assetName,
					description = descValue.Value,
					imageUrl = imageValue.Value,
				}
			end
		end
	end
	return nil
end

return AssetModule

```

### shared/VisionConfig.lua

```lua
return {
    VISION_RANGE = 30, -- Studs
    
    -- Categories of objects NPCs can "see"
    VISIBLE_TAGS = {
        LANDMARK = "landmark",  -- Buildings, stations
        VEHICLE = "vehicle",    -- Cars, trains
        ITEM = "item",         -- Interactive items
        EVENT = "event"        -- Temporary events/activities
    },
    
    -- Cache descriptions for common objects
    ASSET_DESCRIPTIONS = {
        ["TrainStation"] = "A bustling train station with multiple platforms",
        ["Tesla_Cybertruck"] = "A futuristic angular electric vehicle",
        ["HawaiiStore"] = "A colorful shop selling beach gear and souvenirs",
        -- Add more asset descriptions...
    }
} 
```

### shared/ConversationManagerV2.lua

```lua
-- ConversationManagerV2.lua
-- A robust conversation management system for NPC interactions
-- Version: 1.0.0
-- Place in: game.ServerScriptService.Shared

local ConversationManagerV2 = {}
ConversationManagerV2.__index = ConversationManagerV2

-- Constants
local CONVERSATION_TIMEOUT = 300 -- 5 minutes
local MAX_HISTORY_LENGTH = 50
local MAX_CONVERSATIONS_PER_NPC = 5

-- Conversation types enum
ConversationManagerV2.Types = {
    NPC_USER = "npc_user",
    NPC_NPC = "npc_npc",
    GROUP = "group"
}

-- Private storage
local conversations = {}
local activeParticipants = {}

-- Utility functions
local function generateConversationId()
    return game:GetService("HttpService"):GenerateGUID(false)
end

local function getCurrentTime()
    return os.time()
end

local function isValidParticipant(participant)
    return participant and (
        (typeof(participant) == "Instance" and participant:IsA("Player")) or
        (participant.GetParticipantType and participant:GetParticipantType() == "npc")
    )
end

-- Conversation object constructor
function ConversationManagerV2.new()
    local self = setmetatable({}, ConversationManagerV2)
    self:startCleanupTask()
    return self
end

-- Core conversation management functions
function ConversationManagerV2:createConversation(type, participant1, participant2)
    -- Validate participants
    if not isValidParticipant(participant1) or not isValidParticipant(participant2) then
        warn("Invalid participants provided to createConversation")
        return nil
    end

    -- Generate unique ID
    local conversationId = generateConversationId()
    
    -- Create conversation structure
    conversations[conversationId] = {
        id = conversationId,
        type = type,
        participants = {
            [participant1.UserId or participant1.id] = true,
            [participant2.UserId or participant2.id] = true
        },
        messages = {},
        created = getCurrentTime(),
        lastUpdate = getCurrentTime(),
        metadata = {}
    }

    -- Update participant tracking
    local p1Id = participant1.UserId or participant1.id
    local p2Id = participant2.UserId or participant2.id
    
    activeParticipants[p1Id] = activeParticipants[p1Id] or {}
    activeParticipants[p2Id] = activeParticipants[p2Id] or {}
    
    activeParticipants[p1Id][conversationId] = true
    activeParticipants[p2Id][conversationId] = true

    return conversationId
end

function ConversationManagerV2:addMessage(conversationId, sender, message)
    local conversation = conversations[conversationId]
    if not conversation then
        warn("Attempt to add message to nonexistent conversation:", conversationId)
        return false
    end

    -- Add message with metadata
    table.insert(conversation.messages, {
        sender = sender.UserId or sender.id,
        content = message,
        timestamp = getCurrentTime()
    })

    -- Trim history if needed
    if #conversation.messages > MAX_HISTORY_LENGTH then
        table.remove(conversation.messages, 1)
    end

    conversation.lastUpdate = getCurrentTime()
    return true
end

function ConversationManagerV2:getHistory(conversationId, limit)
    local conversation = conversations[conversationId]
    if not conversation then
        return {}
    end

    limit = limit or MAX_HISTORY_LENGTH
    local messages = {}
    local startIndex = math.max(1, #conversation.messages - limit + 1)
    
    for i = startIndex, #conversation.messages do
        table.insert(messages, conversation.messages[i].content)
    end

    return messages
end

function ConversationManagerV2:endConversation(conversationId)
    local conversation = conversations[conversationId]
    if not conversation then
        return false
    end

    -- Remove from participant tracking
    for participantId in pairs(conversation.participants) do
        if activeParticipants[participantId] then
            activeParticipants[participantId][conversationId] = nil
        end
    end

    -- Remove conversation
    conversations[conversationId] = nil
    return true
end

-- Cleanup task
function ConversationManagerV2:startCleanupTask()
    task.spawn(function()
        while true do
            local currentTime = getCurrentTime()
            
            -- Check for expired conversations
            for id, conversation in pairs(conversations) do
                if currentTime - conversation.lastUpdate > CONVERSATION_TIMEOUT then
                    self:endConversation(id)
                end
            end
            
            task.wait(60) -- Run cleanup every minute
        end
    end)
end

-- Utility methods
function ConversationManagerV2:getActiveConversations(participantId)
    return activeParticipants[participantId] or {}
end

function ConversationManagerV2:isParticipantInConversation(participantId, conversationId)
    local conversation = conversations[conversationId]
    return conversation and conversation.participants[participantId] or false
end

function ConversationManagerV2:getConversationMetadata(conversationId)
    local conversation = conversations[conversationId]
    return conversation and conversation.metadata or nil
end

function ConversationManagerV2:updateMetadata(conversationId, key, value)
    local conversation = conversations[conversationId]
    if conversation then
        conversation.metadata[key] = value
        return true
    end
    return false
end

return ConversationManagerV2
```

### shared/PerformanceMonitor.lua

```lua
local PerformanceMonitor = {}
local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")

local metrics = {
    frameRate = {},
    serverLoad = {},
    memoryUsage = {},
    networkBandwidth = {}
}

function PerformanceMonitor:startTracking()
    RunService.Heartbeat:Connect(function()
        -- Track FPS
        table.insert(metrics.frameRate, 1/RunService.Heartbeat:Wait())
        if #metrics.frameRate > 60 then table.remove(metrics.frameRate, 1) end
        
        -- Track Server Stats
        table.insert(metrics.serverLoad, Stats:GetTotalMemoryUsageMb())
        table.insert(metrics.memoryUsage, Stats.DataReceiveKbps)
        table.insert(metrics.networkBandwidth, Stats.DataSendKbps)
        
        -- Keep only last minute of data
        if #metrics.serverLoad > 60 then table.remove(metrics.serverLoad, 1) end
        if #metrics.memoryUsage > 60 then table.remove(metrics.memoryUsage, 1) end
        if #metrics.networkBandwidth > 60 then table.remove(metrics.networkBandwidth, 1) end
    end)
end

function PerformanceMonitor:getMetrics()
    local function average(t)
        local sum = 0
        for _, v in ipairs(t) do sum = sum + v end
        return #t > 0 and sum / #t or 0
    end
    
    return {
        avgFPS = average(metrics.frameRate),
        avgServerLoad = average(metrics.serverLoad),
        avgMemory = average(metrics.memoryUsage),
        avgNetwork = average(metrics.networkBandwidth)
    }
end

return PerformanceMonitor 
```

### shared/ConversationManager.lua

```lua
local ConversationManager = {}

-- Track active conversations and message types
local activeConversations = {
    playerToNPC = {}, -- player UserId -> {npc = npcRef, lastMessage = time}
    npcToNPC = {},    -- npc Id -> {partner = npcRef, lastMessage = time}
    npcToPlayer = {}  -- npc Id -> {player = playerRef, lastMessage = time}
}

-- Message types
local MessageType = {
    SYSTEM = "system",
    CHAT = "chat"
}

function ConversationManager:isSystemMessage(message)
    return string.match(message, "^%[SYSTEM%]")
end

function ConversationManager:canStartConversation(sender, receiver)
    -- Check if either participant is in conversation
    if self:isInConversation(sender) or self:isInConversation(receiver) then
        return false
    end
    return true
end

function ConversationManager:isInConversation(participant)
    local id = self:getParticipantId(participant)
    local participantType = self:getParticipantType(participant)
    
    if participantType == "player" then
        return activeConversations.playerToNPC[id] ~= nil
    else
        return activeConversations.npcToPlayer[id] ~= nil or 
               activeConversations.npcToNPC[id] ~= nil
    end
end

function ConversationManager:lockConversation(sender, receiver)
    local senderId = self:getParticipantId(sender)
    local receiverId = self:getParticipantId(receiver)
    local senderType = self:getParticipantType(sender)
    local receiverType = self:getParticipantType(receiver)
    
    if senderType == "player" and receiverType == "npc" then
        activeConversations.playerToNPC[senderId] = {
            npc = receiver,
            lastMessage = os.time()
        }
        activeConversations.npcToPlayer[receiverId] = {
            player = sender,
            lastMessage = os.time()
        }
    elseif senderType == "npc" and receiverType == "npc" then
        activeConversations.npcToNPC[senderId] = {
            partner = receiver,
            lastMessage = os.time()
        }
        activeConversations.npcToNPC[receiverId] = {
            partner = sender,
            lastMessage = os.time()
        }
    end
end

function ConversationManager:routeMessage(message, sender, intendedReceiver)
    -- Allow system messages to pass through
    if self:isSystemMessage(message) then
        return intendedReceiver
    end
    
    -- Get current conversation partner if any
    local currentPartner = self:getCurrentPartner(sender)
    if currentPartner then
        return currentPartner
    end
    
    -- If no active conversation, try to start one
    if self:canStartConversation(sender, intendedReceiver) then
        self:lockConversation(sender, intendedReceiver)
        return intendedReceiver
    end
    
    return nil
end

-- Helper functions
function ConversationManager:getParticipantId(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return participant.UserId
    else
        return participant.npcId
    end
end

function ConversationManager:getParticipantType(participant)
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return "player"
    else
        return "npc"
    end
end

return ConversationManager 
```

### shared/NPCSystem/NPCManagerV3.lua

```lua
-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local ChatService = game:GetService("Chat")
local RunService = game:GetService("RunService")
local workspace = game:GetService("Workspace")

-- Wait for critical paths and store references
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local services = NPCSystem:WaitForChild("services")
local chat = NPCSystem:WaitForChild("chat")
local config = NPCSystem:WaitForChild("config")

-- Update requires to use correct paths
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local NPCChatHandler = require(chat:WaitForChild("NPCChatHandler"))
local InteractionService = require(services:WaitForChild("InteractionService"))
local LoggerService = require(services:WaitForChild("LoggerService"))
local ModelLoader = require(script.Parent.services.ModelLoader)
local AnimationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.AnimationService)

ModelLoader.init()
LoggerService:info("SYSTEM", string.format("Using ModelLoader v%s", ModelLoader.Version))

LoggerService:info("SYSTEM", "Attempting to load services...")
local success, result = pcall(function()
    local vision = require(services:WaitForChild("VisionService"))
    local movement = require(services:WaitForChild("MovementService"))
    LoggerService:info("SYSTEM", "Services loaded successfully")
    return {vision = vision, movement = movement}
end)

if not success then
    warn("Failed to load services:", result)
end

local VisionService = result.vision
local MovementService = result.movement

-- Initialize Logger
local Logger
local function initializeLogger()
    local success, result = pcall(function()
        if game:GetService("RunService"):IsServer() then
            return require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
        else
            return require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
        end
    end)

    if success then
        Logger = result
        Logger:log("SYSTEM", "Logger initialized successfully")
    else
        -- Create a fallback logger with basic functionality
        Logger = {
            log = function(_, category, message)
                print(string.format("[%s] %s", category, message))
            end,
            error = function(_, message)
                warn("[ERROR] " .. message)
            end,
            warn = function(_, message)
                warn("[WARN] " .. message)
            end,
            debug = function(_, message)
                print("[DEBUG] " .. message)
            end
        }
        
        -- Log the initialization failure using the fallback logger
        Logger:error(string.format("Failed to initialize logger: %s. Using fallback logger.", tostring(result)))
    end

    -- Log the environment information
    local environment = game:GetService("RunService"):IsServer() and "Server" or "Client"
    Logger:log("SYSTEM", string.format("Running in %s environment", environment))
end

initializeLogger()
LoggerService:info("SYSTEM", "NPCManagerV3 module loaded")

local NPCManagerV3 = {}
NPCManagerV3.__index = NPCManagerV3

-- Add singleton instance variable
local instance = nil

-- Add near the top with other local variables
local ThreadManager = {
    activeThreads = {},
    maxThreads = 10
}

-- Add this new function for thread management
function NPCManagerV3:initializeThreadManager()
    -- Initialize thread pool
    self.threadPool = {
        interactionThreads = {},
        movementThreads = {},
        visionThreads = {}
    }
    
    -- Thread limits
    self.threadLimits = {
        interaction = 5,
        movement = 3,
        vision = 2
    }
    
    LoggerService:debug("SYSTEM", "Thread manager initialized")
end

function NPCManagerV3.getInstance()
    if not instance then
        instance = setmetatable({}, NPCManagerV3)
        
        LoggerService:info("SYSTEM", "Initializing NPCManagerV3...")
        
        -- Initialize core components first
        instance.npcs = {}
        instance.responseCache = {}
        instance.activeInteractions = {}
        instance.movementStates = {}
        instance.activeConversations = {}
        instance.lastInteractionTime = {}
        instance.conversationCooldowns = {}
        
        -- Initialize thread manager
        instance:initializeThreadManager()
        
        -- Initialize services
        instance.movementService = MovementService.new()
        instance.interactionController = require(game.ServerScriptService.InteractionController).new()
        
        LoggerService:info("SYSTEM", "Services initialized")
        
        -- Load NPC database
        instance:loadNPCDatabase()
        
        LoggerService:info("SYSTEM", "NPCManagerV3 initialization complete")
    end
    return instance
end

-- Replace .new() with modified version
function NPCManagerV3.new()
    local manager = NPCManagerV3.getInstance()
    -- Ensure database is loaded
    if not manager.databaseLoaded then
        manager:loadNPCDatabase()
        manager.databaseLoaded = true
    end
    return manager
end

local API_URL = "https://roblox.ella-ai-care.com/robloxgpt/v3"
local RESPONSE_COOLDOWN = 1
local FOLLOW_DURATION = 60 -- Follow for 60 seconds by default
local MIN_FOLLOW_DISTANCE = 5 -- Minimum distance to keep from the player
local MEMORY_EXPIRATION = 3600 -- Remember players for 1 hour (in seconds)
local VISION_RANGE = 50 -- Range in studs for NPC vision

local NPC_RESPONSE_SCHEMA = {
	type = "object",
	properties = {
		message = { type = "string" },
		action = {
			type = "object",
			properties = {
				type = {
					type = "string",
					enum = { "follow", "unfollow", "stop_interacting", "none" },
				},
				data = { type = "object" },
			},
			required = { "type" },
			additionalProperties = false,
		},
		internal_state = { type = "object" },
	},
	required = { "message", "action" },
	additionalProperties = false,
}

local NPCChatEvent = ReplicatedStorage:FindFirstChild("NPCChatEvent") or Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

-- Add handler for player messages at initialization
NPCChatEvent.OnServerEvent:Connect(function(player, data)
    NPCManagerV3:getInstance():handlePlayerMessage(player, data)
end)

function NPCManagerV3:handlePlayerMessage(player, data)
    local npcName = data.npcName
    local message = data.message
    
    LoggerService:debug("CHAT", string.format("Received message from player %s to NPC %s: %s",
        player.Name,
        npcName,
        message
    ))
    
    -- Find the NPC by name
    for _, npc in pairs(self.npcs) do
        if npc.displayName == npcName then
            -- Check if the NPC is interacting with this player
            if npc.isInteracting and npc.interactingPlayer == player then
                -- Handle the interaction
                self:handleNPCInteraction(npc, player, message)
            else
                LoggerService:debug("INTERACTION", string.format("NPC %s is not interacting with player %s", 
                    npc.displayName, 
                    player.Name
                ))
            end
            return
        end
    end
    
    LoggerService:error("ERROR", string.format("NPC %s not found when handling player message", npcName))
end

function NPCManagerV3:loadNPCDatabase()
    LoggerService:debug("DATABASE", "Loading NPCs from database...")
    
    -- Get database from Data folder
    local success, database = pcall(function()
        return require(ReplicatedStorage:WaitForChild("Data"):WaitForChild("NPCDatabase"))
    end)
    
    if not success then
        LoggerService:error("DATABASE", "Failed to load NPCDatabase: " .. tostring(database))
        return false
    end
    
    if not database or not database.npcs then
        LoggerService:error("DATABASE", "Invalid database format - missing npcs table")
        return false
    end
    
    LoggerService:debug("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #database.npcs))
    
    for _, npcData in ipairs(database.npcs) do
        if npcData and npcData.displayName then
            self:createNPC(npcData)
        else
            LoggerService:warn("DATABASE", "Skipping invalid NPC data entry")
        end
    end
    
    self.databaseLoaded = true
    LoggerService:debug("DATABASE", "NPC Database loaded successfully")
end

function NPCManagerV3:createNPC(npcData)
    LoggerService:debug("NPC", string.format("Creating NPC: %s", npcData.displayName))
    
    -- Debug log NPC data
    LoggerService:debug("DEBUG", string.format("Creating NPC with data: %s", 
        HttpService:JSONEncode({
            displayName = npcData.displayName,
            abilities = npcData.abilities
        })
    ))

    -- Ensure NPCs folder exists in Workspace (can be created dynamically)
    local NPCsFolder = workspace:FindFirstChild("NPCs")
    if not NPCsFolder or not NPCsFolder:IsA("Folder") then
        NPCsFolder = Instance.new("Folder")
        NPCsFolder.Name = "NPCs"
        NPCsFolder.Parent = workspace
        print("Created 'NPCs' folder in workspace.")
    end

    -- Create and set up NPC model
    if not npcData or not npcData.displayName then
        LoggerService:error("NPC", "Invalid NPC data - missing displayName")
        return
    end
    
    if not npcData.model then
        LoggerService:error("NPC", string.format("Invalid NPC data for %s - missing model ID", npcData.displayName))
        return
    end
    
    LoggerService:debug("NPC", string.format("Loading model for %s with ID: %s", 
        tostring(npcData.displayName), 
        tostring(npcData.model)
    ))
    
    -- Check if Pete's model exists
    if npcData.displayName == "Pete" then
        LoggerService:info("NPC", "Attempting to load Pete's model...")
        LoggerService:info("NPC", "Checking ServerStorage structure:")
        for _, child in ipairs(ServerStorage:GetChildren()) do
            LoggerService:info("NPC", "  - " .. child.Name)
            if child.Name == "Assets" then
                LoggerService:info("NPC", "    Found Assets folder")
                for _, assetChild in ipairs(child:GetChildren()) do
                    LoggerService:info("NPC", "    - " .. assetChild.Name)
                    if assetChild.Name == "npcs" then
                        LoggerService:info("NPC", "      Found npcs folder")
                        for _, npcModel in ipairs(assetChild:GetChildren()) do
                            LoggerService:info("NPC", "      - " .. npcModel.Name)
                        end
                    end
                end
            end
        end

        local peteModel = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
        if peteModel then
            LoggerService:info("NPC", "Found Pete's model in local assets")
            LoggerService:info("NPC", string.format("Model details: Type=%s, Name=%s", peteModel.ClassName, peteModel.Name))
        else
            LoggerService:error("NPC", "Pete's model not found in local assets")
        end
    end
    
    local model = ModelLoader.loadModel(npcData.model)
    if not model then
        LoggerService:error("NPC", string.format("Model not found for NPC: %s", npcData.displayName))
        return
    end

    -- Log model details
    LoggerService:info("NPC", string.format("Loaded model for %s:", npcData.displayName))
    LoggerService:info("NPC", string.format("  - Type: %s", model.ClassName))
    LoggerService:info("NPC", string.format("  - Name: %s", model.Name))
    LoggerService:info("NPC", string.format("  - Children: %d", #model:GetChildren()))
    for _, child in ipairs(model:GetChildren()) do
        LoggerService:info("NPC", string.format("  - Child: %s (%s)", child.Name, child.ClassName))
    end

    local npcModel = model:Clone()
    
    -- Handle R15 model setup
    local function setupR15Model(model)
        local humanoid = model:FindFirstChild("Humanoid")
        if humanoid then
            humanoid.RigType = Enum.HumanoidRigType.R15
        end
        
        -- Ensure all MeshParts are visible
        for _, part in ipairs(model:GetDescendants()) do
            if part:IsA("MeshPart") then
                part.Transparency = 0
            end
        end
    end
    
    -- Ensure model is properly set up
    for _, child in ipairs(npcModel:GetChildren()) do
        if child:IsA("Accessory") then
            LoggerService:debug("NPC", string.format("Setting up accessory: %s", child.Name))
            -- Ensure accessory handle is visible
            local handle = child:FindFirstChild("Handle")
            if handle then
                handle.Transparency = 0
            end
            child.Parent = npcModel
        elseif child:IsA("Shirt") or child:IsA("Pants") or child:IsA("BodyColors") then
            LoggerService:debug("NPC", string.format("Setting up clothing: %s", child.Name))
            child.Parent = npcModel
        end
    end
    
    -- Set up R15 model if needed
    if npcModel:FindFirstChild("UpperTorso") then
        LoggerService:info("NPC", "Setting up R15 model")
        setupR15Model(npcModel)
    end
    
    npcModel.Name = npcData.displayName
    npcModel.Parent = workspace.NPCs

    -- Validate required parts
    local humanoidRootPart = npcModel:FindFirstChild("HumanoidRootPart")
    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    local head = npcModel:FindFirstChild("Head")

    if not humanoidRootPart or not humanoid or not head then
        LoggerService:error("NPC", string.format("NPC model %s is missing essential parts", npcData.displayName))
        npcModel:Destroy()
        return
    end

    -- Set up NPC instance
    local npc = {
        model = npcModel,
        id = npcData.id,
        displayName = npcData.displayName,
        responseRadius = npcData.responseRadius,
        system_prompt = npcData.system_prompt,
        abilities = npcData.abilities or {},
        playersInRange = {},
        lastResponseTime = 0,
        isMoving = false,
        isInteracting = false,
        isFollowing = false,
        followTarget = nil,
        followStartTime = 0,
        memory = {},
        visibleEntities = {},
        interactingPlayer = nil,
        shortTermMemory = {},
        chatHistory = {},
    }

    -- Initialize components
    npcModel.PrimaryPart = humanoidRootPart
    humanoidRootPart.CFrame = CFrame.new(npcData.spawnPosition)
    -- Temporarily disable animations
    AnimationService:applyAnimations(humanoid)
    self:initializeNPCChatSpeaker(npc)
    self:setupClickDetector(npc)

    -- Store NPC reference
    self.npcs[npc.id] = npc
    
    LoggerService:debug("NPC", string.format("NPC added: %s (Total NPCs: %d)", npc.displayName, self:getNPCCount()))
    
    return npc
end

-- Add a separate function to test chat for all NPCs
function NPCManagerV3:testAllNPCChat()
    LoggerService:debug("TEST", "Testing chat for all NPCs...")
    for _, npc in pairs(self.npcs) do
        if npc.model and npc.model:FindFirstChild("Head") then
            -- Try simple chat method only
            game:GetService("Chat"):Chat(npc.model.Head, "Test chat from " .. npc.displayName)
            wait(0.5) -- Small delay between tests
        end
    end
    LoggerService:debug("TEST", "Chat testing complete")
end

function NPCManagerV3:getNPCCount()
	local count = 0
	for _ in pairs(self.npcs) do
		count = count + 1
	end
	LoggerService:debug("DEBUG", string.format("Current NPC count: %d", count))
	return count
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius

	-- Try to parent to HumanoidRootPart, if not available, use any BasePart
	local parent = npc.model:FindFirstChild("HumanoidRootPart") or npc.model:FindFirstChildWhichIsA("BasePart")

	if parent then
		clickDetector.Parent = parent
		LoggerService:debug("INTERACTION", string.format("Set up ClickDetector for %s with radius %d", 
			npc.displayName, 
			npc.responseRadius
		))
	else
		LoggerService:error("ERROR", string.format("Could not find suitable part for ClickDetector on %s", npc.displayName))
		return
	end

	clickDetector.MouseClick:Connect(function(player)
		-- Send system message about player clicking
		local systemMessage = string.format(
			"[SYSTEM] %s has clicked to interact with you. You can start a conversation.",
			player.Name
		)
		self:handleNPCInteraction(npc, player, systemMessage)
	end)
end

function NPCManagerV3:startInteraction(npc1, npc2)
    if not InteractionService:canInteract(npc1, npc2) then
        return false
    end
    
    InteractionService:lockNPCsForInteraction(npc1, npc2)
    
    -- Old interaction code...
end

function NPCManagerV3:endInteraction(npc, participant)
    -- Unlock movement and perform any necessary cleanup
    if npc.model and npc.model:FindFirstChild("Humanoid") then
        npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
        npc.isMovementLocked = false
        LoggerService:debug("MOVEMENT", string.format("Unlocked movement for %s after ending interaction", npc.displayName))
    end

    -- Additional cleanup logic if needed
    -- ...
end

function NPCManagerV3:getCacheKey(npc, player, message)
	local context = {
		npcId = npc.id,
		
		playerId = player.UserId,
		message = message,
		memory = npc.shortTermMemory[player.UserId],
	}
	
	local key = HttpService:JSONEncode(context)
	LoggerService:debug("DEBUG", string.format("Generated cache key for %s and %s", npc.displayName, player.Name))
	return key
end

-- Update helper function to check if participant is NPC
-- Replace the isNPCParticipant function with this improved version
function NPCManagerV3:isNPCParticipant(participant)
    -- Check if it's a Player instance first
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return false
    end
    
    -- Then check for NPC properties
    return participant.Type == "npc" or participant.npcId ~= nil
end

function NPCManagerV3:displayMessage(npc, message, recipient)
    -- Don't propagate error messages between NPCs
    if self:isNPCParticipant(recipient) and message == "I'm having trouble understanding right now." then
        LoggerService:log("CHAT", "Blocking error message propagation between NPCs")
        return
    end

    -- Ensure we have a valid model and head
    if not npc.model or not npc.model:FindFirstChild("Head") then
        LoggerService:error("ERROR", string.format("Cannot display message for %s - missing model or head", npc.displayName))
        return
    end

    -- Create chat bubble
    local success, err = pcall(function()
        game:GetService("Chat"):Chat(npc.model.Head, message)
        LoggerService:debug("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
    end)
    if not success then
        LoggerService:error("ERROR", string.format("Failed to create chat bubble: %s", err))
    end

    -- Handle NPC-to-NPC messages
    if self:isNPCParticipant(recipient) then
        LoggerService:debug("CHAT", string.format("NPC %s to NPC %s: %s",
            npc.displayName,
            recipient.displayName or recipient.Name,
            message
        ))
        
        -- Fire event to all clients for redundancy
        NPCChatEvent:FireAllClients({
            npcName = npc.displayName,
            message = message,
            type = "npc_chat"
        })

        -- Handle recipient response after a small delay
        if recipient.npcId then
            local recipientNPC = self.npcs[recipient.npcId]
            if recipientNPC then
                task.delay(1, function()
                    self:handleNPCInteraction(recipientNPC, self:createMockParticipant(npc), message)
                end)
            end
        end
        return
    end

    -- Handle player messages
    if typeof(recipient) == "Instance" and recipient:IsA("Player") then
        LoggerService:debug("CHAT", string.format("NPC %s sending message to player %s: %s",
            npc.displayName,
            recipient.Name,
            message
        ))
        
        -- Send to player's chat window
        NPCChatEvent:FireClient(recipient, {
            npcName = npc.displayName,
            message = message,
            type = "chat"
        })
        return
    end
end

-- And modify processAIResponse to directly use displayMessage
function NPCManagerV3:processAIResponse(npc, participant, response)
    -- Ignore should_end metadata
    if response.metadata then
        response.metadata.should_end = false
    end

    if response.message then
        self:displayMessage(npc, response.message, participant)
    end

    if response.action then
        LoggerService:debug("ACTION", string.format("Executing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.action)
        ))
        
        -- Handle end_conversation action
        if response.action.type == "end_conversation" then
            self:endInteraction(npc, participant)
        else
            self:executeAction(npc, participant, response.action)
        end
    end

    if response.internal_state then
        LoggerService:debug("STATE", string.format("Updating internal state for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.internal_state)
        ))
        self:updateInternalState(npc, response.internal_state)
    end
end


-- Add this new function to help manage NPC chat speakers
function NPCManagerV3:initializeNPCChatSpeaker(npc)
    if npc and npc.model then
        local createSpeaker = _G.CreateNPCSpeaker
        if createSpeaker then
            createSpeaker(npc.model)
            LoggerService:debug("SYSTEM", string.format("Initialized chat speaker for NPC: %s", npc.displayName))
        end
    end
end

-- Update the displayNPCToNPCMessage function in NPCManagerV3.lua
function NPCManagerV3:testChatBubbles(fromNPC)
    if not fromNPC or not fromNPC.model then
        LoggerService:error("ERROR", "Invalid NPC for chat test")
        return
    end

    local head = fromNPC.model:FindFirstChild("Head")
    if not head then
        LoggerService:error("ERROR", string.format("NPC %s has no Head part!", fromNPC.displayName))
        return
    end

    -- Try each chat method
    LoggerService:debug("TEST", "Testing chat methods...")

    -- Method 1: Direct Chat
    game:GetService("Chat"):Chat(head, "Test 1: Direct Chat")
    wait(2)

    -- Method 2: Legacy Chat
    head.Chatted:Fire("Test 2: Legacy Chat")
    wait(2)

    -- Method 3: BubbleChat
    local Chat = game:GetService("Chat")
    Chat:Chat(head, "Test 3: BubbleChat", Enum.ChatColor.Blue)
    wait(2)

    -- Method 4: ChatService
    local success, err = pcall(function()
        Chat:CreateTalkDialog(head)
        head:SetTextBubble("Test 4: ChatService")
    end)
    
    if not success then
        LoggerService:error("ERROR", "ChatService method failed: " .. tostring(err))
    end

    LoggerService:debug("TEST", "Chat test complete")
end

-- Also update displayNPCToNPCMessage to try all methods
function NPCManagerV3:displayNPCToNPCMessage(fromNPC, toNPC, message)
    if not (fromNPC and toNPC and message) then
        LoggerService:error("ERROR", "Missing required parameters for NPC-to-NPC message")
        return
    end

    LoggerService:debug("CHAT", string.format("NPC %s to NPC %s: %s", 
        fromNPC.displayName or "Unknown",
        toNPC.displayName or "Unknown",
        message
    ))
    
    -- Use the same direct Chat call that worked in our test
    if fromNPC.model and fromNPC.model:FindFirstChild("Head") then
        game:GetService("Chat"):Chat(fromNPC.model.Head, message)
        LoggerService:debug("CHAT", string.format("Created chat bubble for NPC: %s", fromNPC.displayName))
    end
    
    -- Fire event to all clients for redundancy
    NPCChatEvent:FireAllClients({
        npcName = fromNPC.displayName,
        message = message,
        type = "npc_chat"
    })
end

function NPCManagerV3:executeAction(npc, player, action)
    LoggerService:debug("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    if action.type == "stop_talking" then
        -- Stop following if we were following this player
        if npc.isFollowing and npc.followTarget == player then
            LoggerService:debug("MOVEMENT", string.format("Stopping follow as part of ending interaction: %s", player.Name))
            self:stopFollowing(npc)
        end
        -- Let the normal conversation flow handle the ending
    elseif action.type == "follow" then
        LoggerService:debug("MOVEMENT", string.format("Starting to follow player: %s", player.Name))
        self:startFollowing(npc, player)
    elseif action.type == "unfollow" then
        LoggerService:debug("MOVEMENT", string.format("Stopping following player: %s", player.Name))
        self:stopFollowing(npc)
    elseif action.type == "emote" and action.data and action.data.emote then
        LoggerService:debug("ANIMATION", string.format("Playing emote: %s", action.data.emote))
        self:playEmote(npc, action.data.emote)
    elseif action.type == "move" and action.data and action.data.position then
        LoggerService:debug("MOVEMENT", string.format("Moving to position: %s", 
            tostring(action.data.position)
        ))
        self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
    elseif action.type == "none" then
        LoggerService:debug("ACTION", "No action required")
    else
        LoggerService:error("ERROR", string.format("Unknown action type: %s", action.type))
    end
end

function NPCManagerV3:startFollowing(npc, player)
    LoggerService:debug("MOVEMENT", string.format(
        "Starting follow - NPC: %s, Player: %s",
        npc.displayName,
        player and player.Name or "nil"
    ))

    if not player then
        LoggerService:warn("MOVEMENT", "Cannot start following - no player provided")
        return false
    end

    if not player.Character then
        LoggerService:warn("MOVEMENT", string.format(
            "Cannot start following - no character for player %s",
            player.Name
        ))
        return false
    end

    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()
    npc.isWalking = false
    
    -- Pass the player's character as the target
    self:setNPCMovementState(npc, "following", {
        target = player.Character,
        targetId = player.UserId
    })

    -- Explicitly start following behavior
    if self.movementService then
        self.movementService:startFollowing(npc, player.Character, {
            distance = 5,
            updateRate = 0.1
        })
    else
        LoggerService:warn("MOVEMENT", "MovementService not initialized")
        return false
    end

    LoggerService:debug("MOVEMENT", string.format(
        "Follow state set for %s -> %s",
        npc.displayName,
        player.Name
    ))

    return true
end

function NPCManagerV3:updateInternalState(npc, internalState)
	LoggerService:debug("STATE", string.format("Updating internal state for %s: %s",
		npc.displayName,
		HttpService:JSONEncode(internalState)
	))
	
	for key, value in pairs(internalState) do
		npc[key] = value
	end
end

function NPCManagerV3:playEmote(npc, emoteName)
    AnimationService:playEmote(npc, emoteName)
end

function NPCManagerV3:moveNPC(npc, targetPosition)
    LoggerService:debug("MOVEMENT", string.format("Moving %s to position %s", 
        npc.displayName, 
        tostring(targetPosition)
    ))
    
    local Humanoid = npc.model:FindFirstChildOfClass("Humanoid")
    if Humanoid then
        Humanoid:MoveTo(targetPosition)
    else
        LoggerService:error("ERROR", string.format("Cannot move %s (no Humanoid)", npc.displayName))
    end
end

function NPCManagerV3:stopFollowing(npc)
    npc.isFollowing = false
    npc.followTarget = nil
    npc.followStartTime = nil

    -- Tell MovementService to stop following
    if self.movementService then
        self.movementService:stopFollowing(npc)
    end

    -- Stop movement and animations
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        humanoid:MoveTo(npc.model.PrimaryPart.Position)
        AnimationManager:stopAnimations(humanoid)
    end

    -- Update movement state without recursion
    self.movementStates[npc.id] = {
        state = "idle",
        data = {},
        timestamp = os.time()
    }

    LoggerService:debug("MOVEMENT", string.format("%s stopped following and movement halted", npc.displayName))
end

-- Add at the top with other state variables
local recentMessages = {} -- Store recent message IDs to prevent duplicates
local MESSAGE_CACHE_TIME = 1 -- Time in seconds to cache messages

-- Add this helper function
local function generateMessageId(npcId, participantId, message)
    return string.format("%s_%s_%s", npcId, participantId, message)
end

-- Modify handleNPCInteraction to check for duplicates
function NPCManagerV3:handleNPCInteraction(npc, participant, message)
    -- Generate a unique ID for this message
    local messageId = generateMessageId(npc.id, participant.UserId, message)
    
    -- Check if this is a duplicate message
    if recentMessages[messageId] then
        if tick() - recentMessages[messageId] < MESSAGE_CACHE_TIME then
            return -- Skip duplicate message
        end
    end
    
    -- Store message timestamp
    recentMessages[messageId] = tick()
    
    -- Clean up old messages
    for id, timestamp in pairs(recentMessages) do
        if tick() - timestamp > MESSAGE_CACHE_TIME then
            recentMessages[id] = nil
        end
    end
    
    -- Determine participant type
    local participantType = typeof(participant) == "Instance" and participant:IsA("Player") and "player" or "npc"
    local participantId = participantType == "player" and participant.UserId or participant.npcId
    local participantName = participant.Name or participant.displayName

    -- Clean up any existing interactions
    if npc.isInteracting then
        self:endInteraction(npc)
    end
    if participantType == "npc" and participant.isInteracting then
        self:endInteraction(participant)
    end

    LoggerService:debug(
        "Starting interaction - NPC: %s, Participant: %s (%s), Message: %s",
        npc.displayName,
        participantName,
        participantType,
        message
    )

    -- Generate unique interaction ID
    local interactionId = HttpService:GenerateGUID()
    
    -- Check if we can create new interaction thread
    if #self.threadPool.interactionThreads >= self.threadLimits.interaction then
        LoggerService:debug("THREAD", "Maximum interaction threads reached, queuing interaction")
        return
    end
    
    -- Create new thread for interaction
    local thread = task.spawn(function()
        -- Add thread to pool
        table.insert(self.threadPool.interactionThreads, interactionId)
        
        -- Original interaction logic
        local cooldownKey = npc.id .. "_" .. participant.UserId
        local lastInteraction = self.conversationCooldowns[cooldownKey]
        
        if lastInteraction and (os.time() - lastInteraction) < 30 then
            LoggerService:debug(
                "Interaction between %s and %s is on cooldown",
                npc.displayName,
                participant.Name
            )
            return
        end

        -- Lock movement at start of interaction
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            npc.model.Humanoid.WalkSpeed = 0
            npc.isMovementLocked = true
            LoggerService:debug("MOVEMENT", string.format("Locked movement for %s during interaction", npc.displayName))
        end

        local response = NPCChatHandler:HandleChat({
            message = message,
            npc_id = npc.id,
            participant_id = participantType == "player" and participant.UserId or participant.npcId,
            context = {
                participant_type = participantType,
                participant_name = participant.Name,
                is_new_conversation = false,
                interaction_history = {},
                nearby_players = self:getVisiblePlayers(npc),
                npc_location = "Unknown"
            }
        })
        
        if not response then
            -- Unlock movement on failure
            if npc.model and npc.model:FindFirstChild("Humanoid") then
                npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
                npc.isMovementLocked = false
                LoggerService:debug("MOVEMENT", string.format("Unlocked movement for %s after failed interaction", npc.displayName))
            end
            return nil
        end

        -- Process response (this handles chat bubbles and actions)
        self:processAIResponse(npc, participant, response)

        -- Clean up thread when done
        for i, threadId in ipairs(self.threadPool.interactionThreads) do
            if threadId == interactionId then
                table.remove(self.threadPool.interactionThreads, i)
                break
            end
        end
    end)
    
    -- Monitor thread
    task.spawn(function()
        local success, result = pcall(function()
            task.wait(30) -- Timeout after 30 seconds
            if thread then
                task.cancel(thread)
                LoggerService:debug(string.format("Terminated hung interaction thread %s", interactionId))
            end
        end)
        
        if not success then
            LoggerService:error(string.format("Thread monitoring failed: %s", result))
        end
    end)
end

function NPCManagerV3:canNPCsInteract(npc1, npc2)
    -- Check if either NPC is in conversation
    for userId, activeNPC in pairs(self.activeConversations) do
        if activeNPC == npc1 or activeNPC == npc2 then
            LoggerService:debug(string.format(
                "Blocking NPC interaction: %s or %s is busy",
                npc1.displayName,
                npc2.displayName
            ))
            return false
        end
    end
    return true
end

function NPCManagerV3:createMockParticipant(npc)
    return {
        Name = npc.displayName,
        displayName = npc.displayName,
        UserId = npc.id,
        npcId = npc.id,
        Type = "npc",
        GetParticipantType = function() return "npc" end,
        GetParticipantId = function() return npc.id end,
        model = npc.model
    }
end

function NPCManagerV3:getVisiblePlayers(npc)
    local visiblePlayers = {}
    local npcPosition = npc.model and npc.model.PrimaryPart and npc.model.PrimaryPart.Position
    
    if not npcPosition then
        return visiblePlayers
    end
    
    for _, player in ipairs(game:GetService("Players"):GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= 50 then  -- 50 studs visibility range
                table.insert(visiblePlayers, player.Name)
            end
        end
    end
    
    return visiblePlayers
end

function NPCManagerV3:setNPCMovementState(npc, state, data)
    if not npc then return end
    
    -- Update movement state
    self.movementStates[npc.id] = {
        state = state,
        data = data or {},
        timestamp = os.time()
    }
    
    -- Handle state-specific logic without recursion
    if state == "following" then
        npc.isFollowing = true
        npc.followTarget = data.target
        npc.followStartTime = os.time()
    end
    
    LoggerService:debug("MOVEMENT", string.format(
        "Set %s movement state to %s",
        npc.displayName,
        state
    ))
end

function NPCManagerV3:getNPCMovementState(npc)
    return self.movementStates[npc.id]
end

-- Add thread cleanup function
function NPCManagerV3:cleanupThreads()
    for threadType, threads in pairs(self.threadPool) do
        for i = #threads, 1, -1 do
            local threadId = threads[i]
            if not ThreadManager.activeThreads[threadId] then
                table.remove(threads, i)
                LoggerService:debug("THREAD", string.format("Cleaned up inactive %s thread %s", threadType, threadId))
            end
        end
    end
end

-- Add periodic thread cleanup
task.spawn(function()
    while true do
        task.wait(60) -- Clean up every minute
        NPCManagerV3:getInstance():cleanupThreads()
    end
end)

function NPCManagerV3:updateNPCPosition(npc)
    if npc.movementState == "free" then
        local randomPos = MovementService:getRandomPosition(npc.spawnPosition, npc.wanderRadius)
        MovementService:moveNPCToPosition(npc, randomPos)
    end
end

-- Initialize NPC with animations
function NPCManagerV3:initializeNPC(npc)
    local humanoid = npc:FindFirstChildOfClass("Humanoid")
    if humanoid then
        AnimationService:applyAnimations(humanoid)
    end
end

return NPCManagerV3

```

### shared/NPCSystem/NPCDatabase.lua

```lua
return {
    npcs = {
        {
            id = "8c9bba8d-4f9a-4748-9e75-1334e48e2e66",
            displayName = "Diamond",
            model = "4446576906",
            spawnPosition = Vector3.new(5, 17, -10),
            responseRadius = 20,
            abilities = {"move", "chat"},
            system_prompt = "You are Diamond, a friendly NPC..."
        },
        -- Other NPCs...
    }
} 
```

### shared/NPCSystem/config.lua

```lua
local Config = {}

-- Toggle this to switch between legacy and new action systems
Config.UseNewActionSystem = false

return Config 
```

### shared/NPCSystem/services/MovementService.lua

```lua
-- MovementService.lua
local LoggerService = {
    debug = function(_, category, message) 
        print(string.format("[DEBUG] [%s] %s", category, message))
    end,
    warn = function(_, category, message)
        warn(string.format("[WARN] [%s] %s", category, message))
    end
}

local MovementService = {}
MovementService.__index = MovementService

function MovementService.new()
    local self = setmetatable({}, MovementService)
    self.followThreads = {}
    LoggerService:debug("MOVEMENT", "New MovementService instance created")
    return self
end

function MovementService:startFollowing(npc, target, options)
    LoggerService:debug("MOVEMENT", string.format(
        "Starting follow behavior - NPC: %s, Target: %s",
        npc.displayName,
        target.Name
    ))

    local followDistance = options and options.distance or 5
    local updateRate = options and options.updateRate or 0.1

    -- Clean up existing thread if any
    self:stopFollowing(npc)

    -- Create new follow thread
    local thread = task.spawn(function()
        while true do
            if not npc.model or not target then break end
            
            local npcRoot = npc.model:FindFirstChild("HumanoidRootPart")
            local targetRoot = target:FindFirstChild("HumanoidRootPart")
            
            if npcRoot and targetRoot then
                local distance = (npcRoot.Position - targetRoot.Position).Magnitude
                
                if distance > followDistance then
                    local humanoid = npc.model:FindFirstChild("Humanoid")
                    if humanoid then
                        -- Set appropriate walk speed
                        humanoid.WalkSpeed = distance > 20 and 16 or 8
                        humanoid:MoveTo(targetRoot.Position)
                    end
                end
            end
            
            task.wait(updateRate)
        end
    end)

    -- Store thread reference
    self.followThreads[npc] = thread
end

function MovementService:stopFollowing(npc)
    if self.followThreads[npc] then
        -- Cancel the follow thread
        task.cancel(self.followThreads[npc])
        self.followThreads[npc] = nil
        
        -- Stop the humanoid
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            local humanoid = npc.model:FindFirstChild("Humanoid")
            humanoid:MoveTo(npc.model.PrimaryPart.Position)
        end
        
        LoggerService:debug("MOVEMENT", string.format("Stopped following for %s", npc.displayName))
    end
end

function MovementService:moveNPCToPosition(npc, targetPosition)
    if not npc or not npc.model then return end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then return end
    
    -- Get current position
    local currentPosition = npc.model:GetPrimaryPartCFrame().Position
    local distance = (targetPosition - currentPosition).Magnitude
    
    -- Set appropriate walk speed
    if distance > 20 then
        humanoid.WalkSpeed = 16  -- Run speed
    else
        humanoid.WalkSpeed = 8   -- Walk speed
    end
    
    -- Move to position
    humanoid:MoveTo(targetPosition)
end

function MovementService:getRandomPosition(center, radius)
    local angle = math.random() * math.pi * 2
    local distance = math.sqrt(math.random()) * radius
    
    return Vector3.new(
        center.X + math.cos(angle) * distance,
        center.Y,
        center.Z + math.sin(angle) * distance
    )
end

return MovementService 
```

### shared/NPCSystem/services/VisionService.lua

```lua
-- VisionService.lua
local VisionService = {}

function VisionService:isInRange(npc1, npc2, radius)
    return true
end

return VisionService 
```

### shared/NPCSystem/services/ActionService.lua

```lua
local ActionService = {}

local LoggerService = {
    debug = function(_, category, message)
        print(string.format("[DEBUG] [%s] %s", category, message))
    end,
    warn = function(_, category, message)
        warn(string.format("[WARN] [%s] %s", category, message))
    end
}

local MovementService = require(ReplicatedStorage.Shared.NPCSystem.services.MovementService)

-- Follow Action
function ActionService.follow(npc, target, options)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is following target %s", npc.displayName, target.Name))
    if npc and target then
        -- Delegate to MovementService for follow behavior
        MovementService:startFollowing(npc, target, options)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Target provided for follow action")
    end
end

-- Unfollow Action
function ActionService.unfollow(npc)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s stopped following", npc.displayName))
    if npc then
        -- Delegate to MovementService to stop following
        MovementService:stopFollowing(npc)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC provided for unfollow action")
    end
end

-- Chat Action
function ActionService.chat(npc, message)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is chatting: %s", npc.displayName, message))
    if npc and message then
        -- Example chat bubble logic
        local chatEvent = game.ReplicatedStorage:FindFirstChild("NPCChatEvent")
        if chatEvent then
            chatEvent:FireAllClients(npc, message)
        else
            LoggerService:warn("ACTION_SERVICE", "NPCChatEvent not found in ReplicatedStorage")
        end
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Message provided for chat action")
    end
end

-- Placeholder for additional actions
function ActionService.moveTo(npc, position)
    LoggerService:debug("ACTION_SERVICE", string.format("NPC %s is moving to position: %s", npc.displayName, tostring(position)))
    if npc and position then
        MovementService:moveNPCToPosition(npc, position)
    else
        LoggerService:warn("ACTION_SERVICE", "Invalid NPC or Position provided for moveTo action")
    end
end

return ActionService
```

### shared/NPCSystem/services/LoggerService.lua

```lua
print("LoggerService loaded")

local LoggerService = {}

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR"
export type LogCategory = "SYSTEM" | "NPC" | "CHAT" | "INTERACTION" | "MOVEMENT" | "ANIMATION" | "DATABASE" | "API"

local config = {
    enabled = true,
    minLevel = "DEBUG",
    enabledCategories = {
        SYSTEM = true,
        NPC = true,
        CHAT = true,
        INTERACTION = true,
        MOVEMENT = true,
        ANIMATION = true,
        DATABASE = true,
        API = true
    },
    timeFormat = "%Y-%m-%d %H:%M:%S",
    outputToFile = false,
    outputPath = "logs/"
}

local levelPriority = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4
}

function LoggerService:shouldLog(level: LogLevel, category: LogCategory): boolean
    if not config.enabled then return false end
    if not config.enabledCategories[category] then return false end
    return levelPriority[level] >= levelPriority[config.minLevel]
end

function LoggerService:formatMessage(level: LogLevel, category: LogCategory, message: string): string
    local timestamp = os.date(config.timeFormat)
    return string.format("[%s] [%s] [%s] %s", timestamp, level, category, message)
end

function LoggerService:log(level: LogLevel, category: LogCategory, message: string)
    if not self:shouldLog(level, category) then return end
    
    local formattedMessage = self:formatMessage(level, category, message)
    print(formattedMessage)
    
    if config.outputToFile then
        -- TODO: Implement file output
    end
end

-- Convenience methods
function LoggerService:debug(category: LogCategory, message: string)
    self:log("DEBUG", category, message)
end

function LoggerService:info(category: LogCategory, message: string)
    self:log("INFO", category, message)
end

function LoggerService:warn(category: LogCategory, message: string)
    self:log("WARN", category, message)
end

function LoggerService:error(category: LogCategory, message: string)
    self:log("ERROR", category, message)
end

-- Configuration methods
function LoggerService:setMinLevel(level: LogLevel)
    config.minLevel = level
end

function LoggerService:enableCategory(category: LogCategory)
    config.enabledCategories[category] = true
end

function LoggerService:disableCategory(category: LogCategory)
    config.enabledCategories[category] = false
end

return LoggerService 
```

### shared/NPCSystem/services/ModelLoader.lua

```lua
local ModelLoader = {}
ModelLoader.Version = "1.0.1"

local ServerStorage = game:GetService("ServerStorage")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

function ModelLoader.init()
    LoggerService:info("SYSTEM", string.format("ModelLoader v%s initialized", ModelLoader.Version))
    
    -- Check initial folder structure
    if ServerStorage:FindFirstChild("Assets") then
        LoggerService:info("MODEL", "Found Assets folder in ServerStorage")
        if ServerStorage.Assets:FindFirstChild("npcs") then
            LoggerService:info("MODEL", "Found npcs folder in Assets")
            local models = ServerStorage.Assets.npcs:GetChildren()
            LoggerService:info("MODEL", string.format("Found %d models in npcs folder:", #models))
            for _, model in ipairs(models) do
                LoggerService:info("MODEL", " - " .. model.Name)
            end
        else
            LoggerService:error("MODEL", "npcs folder not found in Assets")
        end
    else
        LoggerService:error("MODEL", "Assets folder not found in ServerStorage")
    end
end

function ModelLoader.loadModel(modelId, modelType)
    LoggerService:info("MODEL", string.format("ModelLoader v%s - Loading model: %s", ModelLoader.Version, modelId))
    
    -- Find all Assets folders
    local assetsFolders = {}
    for _, child in ipairs(ServerStorage:GetChildren()) do
        if child.Name == "Assets" then
            table.insert(assetsFolders, child)
        end
    end
    
    LoggerService:info("MODEL", string.format("Found %d Assets folders", #assetsFolders))
    
    -- Use only the first Assets folder and warn about duplicates
    if #assetsFolders > 1 then
        LoggerService:warn("MODEL", "Multiple Assets folders found - using only the first one")
        -- Remove extra Assets folders
        for i = 2, #assetsFolders do
            LoggerService:warn("MODEL", string.format("Removing duplicate Assets folder %d", i))
            assetsFolders[i]:Destroy()
        end
    end
    
    local assetsFolder = assetsFolders[1]
    if not assetsFolder then
        LoggerService:error("MODEL", "No Assets folder found")
        return nil
    end
    
    local npcsFolder = assetsFolder:FindFirstChild("npcs")
    if not npcsFolder then
        LoggerService:error("MODEL", "No npcs folder found in Assets")
        return nil
    end
    
    local model = npcsFolder:FindFirstChild(modelId)
    if not model then
        -- Try loading from RBXM file
        local success, result = pcall(function()
            return game:GetService("InsertService"):LoadLocalAsset(string.format("%s/src/assets/npcs/%s.rbxm", game:GetService("ServerScriptService").Parent.Parent.Name, modelId))
        end)
        if success and result then
            model = result
        end
    end
    
    if model and model:IsA("Model") then
        LoggerService:info("MODEL", string.format("Found model: Type=%s, Name=%s, Children=%d", 
            model.ClassName, model.Name, #model:GetChildren()))
        
        -- Log all model parts
        for _, child in ipairs(model:GetChildren()) do
            LoggerService:debug("MODEL", string.format("  - %s (%s)", child.Name, child.ClassName))
        end
        
        return model:Clone()
    end
    
    LoggerService:error("MODEL", string.format("Model %s not found", modelId))
    return nil
end

return ModelLoader 
```

### shared/NPCSystem/services/AnimationService.lua

```lua
local AnimationManager = {}
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Different animation IDs for R6 and R15
local animations = {
    R6 = {
        idle = "rbxassetid://180435571",    -- R6 idle
        walk = "rbxassetid://180426354",    -- R6 walk
        run = "rbxassetid://180426354"      -- R6 run (same as walk but faster)
    },
    R15 = {
        idle = "rbxassetid://507766666",    -- R15 idle
        walk = "rbxassetid://507777826",    -- R15 walk
        run = "rbxassetid://507767714"      -- R15 run
    }
}

-- Table to store current animations per humanoid
local currentAnimations = {}

-- Add this helper function at the top
local function isMoving(humanoid)
    -- Check if the humanoid is actually moving by looking at velocity
    local rootPart = humanoid.Parent and humanoid.Parent:FindFirstChild("HumanoidRootPart")
    if rootPart then
        -- Use velocity magnitude to determine if actually moving
        return rootPart.Velocity.Magnitude > 0.1
    end
    return false
end

function AnimationManager:getRigType(humanoid)
    if not humanoid then return nil end
    
    local character = humanoid.Parent
    if character then
        if character:FindFirstChild("UpperTorso") then
            return "R15"
        else
            return "R6"
        end
    end
    return nil
end

function AnimationManager:applyAnimations(humanoid)
    if not humanoid then
        LoggerService:error("ANIMATION", "Cannot apply animations: Humanoid is nil")
        return
    end
    
    local rigType = self:getRigType(humanoid)
    if not rigType then
        LoggerService:error("ANIMATION", string.format("Cannot determine rig type for humanoid: %s", 
            humanoid.Parent and humanoid.Parent.Name or "unknown"))
        return
    end
    
    LoggerService:debug("ANIMATION", string.format("Detected %s rig for %s", 
        rigType, humanoid.Parent.Name))
    
    -- Get or create animator
    local animator = humanoid:FindFirstChild("Animator")
    if not animator then
        animator = Instance.new("Animator")
        animator.Parent = humanoid
    end
    
    -- Initialize animations table for this humanoid
    if not currentAnimations[humanoid] then
        currentAnimations[humanoid] = {
            rigType = rigType,
            tracks = {}
        }
    end
    
    -- Preload all animations for this rig type
    for name, id in pairs(animations[rigType]) do
        local animation = Instance.new("Animation")
        animation.AnimationId = id
        local track = animator:LoadAnimation(animation)
        currentAnimations[humanoid].tracks[name] = track
        LoggerService:debug("ANIMATION", string.format("Loaded %s animation for %s (%s)", 
            name, humanoid.Parent.Name, rigType))
    end
    
    -- Connect to state changes for animation updates
    humanoid.StateChanged:Connect(function(_, new_state)
        if (new_state == Enum.HumanoidStateType.Running or 
            new_state == Enum.HumanoidStateType.Walking) and 
            isMoving(humanoid) then
            -- Only play walk/run if actually moving
            local speed = humanoid.WalkSpeed
            self:playAnimation(humanoid, speed > 8 and "run" or "walk")
        else
            -- Play idle for any other state or when not moving
            self:playAnimation(humanoid, "idle")
        end
    end)
    
    -- Also connect to physics updates to catch movement changes
    local rootPart = humanoid.Parent and humanoid.Parent:FindFirstChild("HumanoidRootPart")
    if rootPart then
        game:GetService("RunService").Heartbeat:Connect(function()
            if humanoid.Parent and not humanoid.Parent.Parent then return end -- Check if destroyed
            
            if isMoving(humanoid) then
                local speed = humanoid.WalkSpeed
                self:playAnimation(humanoid, speed > 8 and "run" or "walk")
            else
                self:playAnimation(humanoid, "idle")
            end
        end)
    end
    
    -- Start with idle animation
    self:playAnimation(humanoid, "idle")
end

function AnimationManager:playAnimation(humanoid, animationName)
    if not humanoid or not currentAnimations[humanoid] then return end
    
    local animData = currentAnimations[humanoid]
    local track = animData.tracks and animData.tracks[animationName]
    
    if not track then
        LoggerService:error("ANIMATION", string.format("No %s animation track found for %s", 
            animationName, humanoid.Parent.Name))
        return
    end
    
    -- Stop other animations
    for name, otherTrack in pairs(animData.tracks) do
        if name ~= animationName and otherTrack.IsPlaying then
            otherTrack:Stop()
        end
    end
    
    -- Play the requested animation if it's not already playing
    if not track.IsPlaying then
        -- Adjust speed for running
        if animationName == "walk" and humanoid.WalkSpeed > 8 then
            track:AdjustSpeed(1.5)  -- Speed up walk animation for running
        else
            track:AdjustSpeed(1.0)  -- Normal speed for other animations
        end
        
        track:Play()
        LoggerService:debug("ANIMATION", string.format("Playing %s animation for %s", 
            animationName, humanoid.Parent.Name))
    end
end

function AnimationManager:stopAnimations(humanoid)
    if currentAnimations[humanoid] and currentAnimations[humanoid].tracks then
        for _, track in pairs(currentAnimations[humanoid].tracks) do
            track:Stop()
        end
        LoggerService:debug("ANIMATION", string.format("Stopped all animations for %s", 
            humanoid.Parent.Name))
    end
end

function AnimationManager:playEmote(npc, emoteName)
    local Animator = npc.model:FindFirstChildOfClass("Animator")
    if Animator then
        local animation = ServerStorage.Animations:FindFirstChild(emoteName)
        if animation then
            Animator:LoadAnimation(animation):Play()
            LoggerService:debug("ANIMATION", string.format("Playing emote %s for %s", emoteName, npc.displayName))
        else
            LoggerService:error("ERROR", string.format("Animation not found: %s", emoteName))
        end
    end
end

return AnimationManager
```

### shared/NPCSystem/services/InteractionService.lua

```lua
-- InteractionService.lua
local InteractionService = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local LoggerService = require(NPCSystem.services.LoggerService)

function InteractionService:checkRangeAndEndConversation(npc1, npc2)
    if not npc1.model or not npc2.model then return end
    if not npc1.model.PrimaryPart or not npc2.model.PrimaryPart then return end

    local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
    if distance > npc1.responseRadius then
        LoggerService:log("INTERACTION", string.format("%s and %s are out of range, ending conversation",
            npc1.displayName, npc2.displayName))
        return true
    end
    return false
end

function InteractionService:canInteract(npc1, npc2)
    -- Check if either NPC is already in conversation
    if npc1.inConversation or npc2.inConversation then
        return false
    end
    
    -- Check abilities
    if not npc1.abilities or not npc2.abilities then
        return false
    end
    
    -- Check if they can chat
    if not (table.find(npc1.abilities, "chat") and table.find(npc2.abilities, "chat")) then
        return false
    end
    
    return true
end

function InteractionService:lockNPCsForInteraction(npc1, npc2)
    npc1.inConversation = true
    npc2.inConversation = true
    npc1.movementState = "locked"
    npc2.movementState = "locked"
end

function InteractionService:unlockNPCsAfterInteraction(npc1, npc2)
    npc1.inConversation = false
    npc2.inConversation = false
    npc1.movementState = "free"
    npc2.movementState = "free"
end

return InteractionService 
```

### shared/NPCSystem/actions/ActionRouter.lua

```lua
local ActionRouter = {}

local ActionHandlers = {}
local ActionService = require(ReplicatedStorage.Shared.NPCSystem.services.ActionService)

-- Function to register action handlers
function ActionRouter:registerAction(actionType, handler)
    ActionHandlers[actionType] = handler
end

-- Function to route actions to the correct handler
function ActionRouter:routeAction(npc, participant, action)
    local actionType = action and action.type

    if not actionType then
        warn("[ActionRouter] Invalid action format:", action)
        return
    end

    local handler = ActionHandlers[actionType]
    if handler then
        print("[ActionRouter] Executing action:", actionType)
        handler(npc, participant, action.data)
    else
        warn("[ActionRouter] No handler registered for action:", actionType)
    end
end

-- Initialize action handlers
function ActionRouter:initialize()
    -- Register a "follow" action
    self:registerAction("follow", function(npc, participant, data)
        local target = participant -- Assuming the participant is the follow target
        ActionService.follow(npc, target, data)
    end)

    -- Register an "unfollow" action
    self:registerAction("unfollow", function(npc, _, _)
        ActionService.unfollow(npc)
    end)

    -- Register a "chat" action
    self:registerAction("chat", function(npc, _, data)
        if data.message then
            ActionService.chat(npc, data.message)
        else
            warn("[ActionRouter] Missing message for chat action")
        end
    end)
end

return ActionRouter
```

### shared/NPCSystem/chat/V3ChatClient.lua

```lua
-- Basic V3 client for fallback
local V3ChatClient = {}

function V3ChatClient:SendMessage(request)
    -- Basic V3 implementation
    return {
        message = "V3 Fallback: " .. request.message,
        action = { type = "none" }
    }
end

return V3ChatClient 
```

### shared/NPCSystem/chat/V4ChatClient.lua

```lua
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
    
    -- Check if the AI response includes an action to end the conversation
    if decoded.action and decoded.action.type == "end_conversation" then
        decoded.metadata.should_end = true
    else
        decoded.metadata.should_end = false
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
```

### shared/NPCSystem/chat/NPCChatHandler.lua

```lua
-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.Shared.NPCSystem.chat.V3ChatClient)
local HttpService = game:GetService("HttpService")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

local recentResponses = {}
local RESPONSE_CACHE_TIME = 1

function NPCChatHandler:HandleChat(request)
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
    
    LoggerService:debug("CHAT", string.format("NPCChatHandler: Received request %s", 
        HttpService:JSONEncode(request)))
    
    LoggerService:debug("CHAT", "NPCChatHandler: Attempting V4")
    local response = self:attemptV4Chat(request)
    
    if response then
        LoggerService:debug("CHAT", string.format("NPCChatHandler: V4 succeeded %s", 
            HttpService:JSONEncode(response)))
        return response
    end
    
    return nil
end

function NPCChatHandler:attemptV4Chat(request)
    local v4Response = V4ChatClient:SendMessage(request)
    
    if v4Response then
        -- Ensure we have a valid message
        if not v4Response.message then
            v4Response.message = "..."
        end
        return v4Response
    end
    
    -- If V4 failed, return error response
    return {
        message = "...",
        action = { type = "none" },
        metadata = {}
    }
end

return NPCChatHandler 
```

### shared/NPCSystem/chat/ChatUtils.lua

```lua
local ChatUtils = {}

local HttpService = game:GetService("HttpService")
local API_BASE_URL = "https://roblox.ella-ai-care.com"

function ChatUtils:MakeRequest(endpoint, payload, method)
    method = method or (payload and "POST" or "GET")
    
    local requestConfig = {
        Url = API_BASE_URL .. endpoint,
        Method = method,
        Headers = {
            ["Content-Type"] = "application/json"
        }
    }
    
    if payload then
        requestConfig.Body = HttpService:JSONEncode(payload)
    end
    
    local success, response = pcall(function()
        return HttpService:RequestAsync(requestConfig)
    end)
    
    if success and response.Success then
        local decoded = HttpService:JSONDecode(response.Body)
        if decoded and not decoded.action then
            decoded.action = {
                type = "none",
                data = {}
            }
        end
        return decoded
    else
        warn("API request failed:", response.StatusCode, response.StatusMessage)
        warn("Request URL:", requestConfig.Url)
        warn("Request payload:", requestConfig.Body)
        if response.Body then
            warn("Response body:", response.Body)
        end
        error("Failed to make API request: " .. tostring(response.StatusMessage))
    end
end

return ChatUtils 
```

### shared/NPCSystem/config/NPCConfig.lua

```lua
return {
    API_BASE_URL = "https://roblox.ella-ai-care.com",
    DEFAULT_TIMEOUT = 30,
    RATE_LIMIT = {
        MAX_REQUESTS = 10,
        WINDOW_SECONDS = 60
    },
    CONVERSATION_SETTINGS = {
        MAX_LENGTH = 100,
        IDLE_TIMEOUT = 300,
        MAX_ACTIVE_CONVERSATIONS = 5
    }
} 
```

### shared/NPCSystem/config/PerformanceConfig.lua

```lua
local PerformanceConfig = {
    -- Logging Settings
    Logging = {
        Enabled = true,
        MinLevel = 4, -- 1=DEBUG, 2=INFO, 3=WARN, 4=ERROR
        BatchSize = 10,
        FlushInterval = 1, -- seconds
        DetailedAssets = false, -- Detailed asset logging
        AnimationErrors = false, -- Log animation state errors
        BatchProcessing = true,  -- Enable log batching
        DebugNPCStates = false  -- Detailed NPC state logging
    },

    -- NPC Settings
    NPC = {
        -- Movement
        MovementEnabled = true,
        UpdateInterval = 5, -- seconds
        MovementChance = 0.8, -- 80% chance to move
        MovementRadius = 10, -- studs
        
        -- Range Checking
        RangeCheckInterval = 5, -- seconds
        ProximityEnabled = true,
        ProximityRadius = 4, -- studs
        
        -- Vision & Raycasting
        VisionEnabled = false,
        VisionUpdateRate = 0.5, -- seconds between vision updates
        MaxVisionDistance = 50, -- max raycast distance
        RaycastBatchSize = 5,  -- number of raycasts per frame
        SkipOccludedTargets = true, -- skip targets behind walls
        VisionConeAngle = 120, -- vision cone in degrees
        
        -- Animations
        AnimationsEnabled = true,
        AnimationDebounce = 0.2, -- seconds
        
        -- Performance Tuning
        MaxActiveNPCs = 10,    -- Maximum NPCs active at once
        CullDistance = 100,    -- Distance at which to disable NPCs
        LODDistance = 50      -- Distance for lower detail
    },

    -- Thread Management
    Threading = {
        MaxThreads = 10,
        ThreadTimeout = 5, -- seconds
        EnableParallel = true,
        ThreadPoolSize = 5
    },

    -- Chat Settings
    Chat = {
        Enabled = true,
        CooldownTime = 1, -- seconds between messages
        MaxMessagesPerMinute = 30,
        BatchProcessing = true,
        BatchSize = 5,
        LogAllMessages = true, -- Log all chat messages
        DetailedLogging = true -- Log detailed chat info
    },

    -- Performance Monitoring
    Monitoring = {
        Enabled = true,
        LogInterval = 60, -- Log metrics every 60 seconds
        AlertThresholds = {
            minFPS = 30,
            maxMemoryMB = 1000,
            maxNetworkKbps = 1000
        }
    }
}

return PerformanceConfig 
```

### shared/NPCSystem/config/LettaConfig.lua

```lua
return {
    BASE_URL = "https://roblox.ella-ai-care.com",
    ENDPOINTS = {
        CHAT = "/letta/v1/chat/v2",
        AGENTS = "/letta/v1/agents"
    },
    DEFAULT_HEADERS = {
        ["Content-Type"] = "application/json"
    }
} 
```

### shared/NPCSystem/config/InteractionConfig.lua

```lua
 
```

### data/AssetDatabase.lua

```lua
return {
    assets = {
        {
            assetId = "113047419407707",
            name = "Addidas Sweats",
            description = "The image features a pair of black pants hanging on a gray hanger. The pants are sleek and shiny, with two prominent white stripes running horizontally across the lower half. The hanger adds a simple touch, allowing for easy display. The overall design gives a modern and stylish vibe, suitable for various avatars.",
        },
        {
            assetId = "94427113881273",
            name = "Cap",
            description = "The Roblox asset features a stylish cap with a classic design. The top is glossy black, while the brim and lower portion are a vibrant red plaid pattern. A prominent white \"R\" logo is displayed on the front, adding a distinctive Roblox flair. The cap exudes a playful yet trendy vibe, perfect for avatar customization.",
        },
        {
            assetId = "117944303189815",
            name = "Felepe",
            description = "The Roblox asset features a stylized, cartoonish human head stylized after Felepe. It has a smooth, predominantly white surface with exaggerated facial features. The eyes are simple black dots, while the lips are a prominent shade of red. A patch of light brown hair is visible on one side, adding to its quirky appearance.",
        },
        {
            assetId = "109742670646912",
            name = "Medkit",
            description = "This Med Kit is compact and reliable, designed to treat injuries from accidents and damage. It contains bandages, antiseptic, and basic supplies to restore health quickly. Lightweight and easy to carry, it’s perfect for adventurers needing quick healing on the go.",
        },
        {
            assetId = "4446576906",
            name = "Noob2",
            description = "The humanoid asset features a simple, blocky character design. It has a round, yellow head with a cheerful smile, and a blue short-sleeved shirt. The arms are wide and yellow, while the legs are green, creating a bright, colorful appearance. The character embodies a playful, cartoonish style typical of Roblox avatars.",
        },
        {
            assetId = "109728553304180",
            name = "Pete burned bald",
            description = "The Roblox asset features a blocky character with a bright red head and a cheerful smile. Dressed in a sleek black tracksuit, it showcases red accents on the sleeves. The outfit includes an \"Adidas\" logo on the pants, emphasizing a sporty look. The design is simple yet eye-catching, embodying a playful aesthetic typical of Roblox avatars.",
        },
        {
            assetId = "115911040617133",
            name = "Pete burned with hair",
            description = "The Roblox asset features a blocky character with a cheerful smile and red head. It has short, brown hair and is dressed in a sleek black tracksuit adorned with white stripes and the Adidas logo. The character's arms are red, providing a unique color contrast, while the entire outfit looks sporty and stylish.",
        },
        {
            assetId = "138986009632421",
            name = "Pete no glasses or hat",
            description = "The Roblox asset features a blocky character with a cheerful red face and a bright blonde hairstyle. Dressed in a sleek black tracksuit with the adidas logo on the sides, it has white stripes down the pants. The character’s arms are slightly elongated, emphasizing the iconic Roblox style, and it stands firmly with a smiling expression.",
        },
        {
            assetId = "109968354800849",
            name = "Pete sunburned",
            description = "The Roblox asset features a character with a distinctive look: a bright red head with a smiling face and oversized purple sunglasses. Its spiky blonde hair adds flair. Dressed in a sleek black Adidas tracksuit highlighted with red accents, the character wears matching sporty footwear, embodying a stylish yet playful vibe.",
        },
        {
            assetId = "87326615665609",
            name = "Pete with glasses",
            description = "The Roblox character features a blocky design with a cheerful smiley face and stylish purple sunglasses. Dressed in a sleek black tracksuit adorned with the Adidas logo, the outfit includes white accents down the sides. The character's hairstyle is a tousled brown, enhancing the sporty, laid-back appearance.",
        },
        {
            assetId = "90229749986361",
            name = "Pete with visor",
            description = "The Roblox character features a yellow smiley face with sunglasses, a hairstyle with brown spikes, and a sporty look. It wears a black tracksuit adorned with white Adidas stripes and a logo. The outfit is complemented by white shoes, giving a sleek and modern athletic appearance. The overall vibe is casual and stylish.",
        },
        {
            assetId = "96144138651755",
            name = "Pete's Merch Stand",
            description = "Pete’s Merch Stand is a wooden structure resembling a rustic fireplace mantel. It features a dark wood finish with detailed grain patterns for a realistic look. The design includes a flat top surface for displaying goods and sturdy, block-like legs for stability. Its simple yet functional style makes it ideal for a variety of in-game environments.",
        },
        {
            assetId = "106403462264097",
            name = "Regenerative Syringe",
            description = "This large syringe has a vibrant green liquid inside. Its barrel is sleek and cylindrical, topped with a metallic plunger. The syringe has black grip handles on either side, enhancing usability. The needle is long and slender, adding a realistic touch. Overall, it conveys a medical theme.",
        },
        {
            assetId = "121855855020853",
            name = "Roblox Cap",
            description = "The asset is a stylish black cap with a curved brim. It features the Roblox logo prominently displayed in white on the front, with the tagline \"Powering Imagination\" beneath it. The design is sleek and minimalistic, giving it a modern appeal. The cap has a smooth texture and a traditional baseball cap shape.",
        },
        {
            assetId = "106036302133738",
            name = "Roblox Visor",
            description = "The image features a white visor with a wide brim and a simple yet distinctive design. Prominently displayed on the front is the red \"ROBLOX\" logo, giving it a playful and recognizable appearance. The visor has a smooth texture and a curved shape, ideal for trendy Roblox avatars. Its minimalist style enhances its appeal.",
        },
        {
            assetId = "91282954419056",
            name = "Shirt with face",
            description = "The Roblox asset features a rectangular black box with a cheerful yellow smiley face in the center. The face displays wide eyes and a big grin. It has two vertical gray sides and a simple hook on top for hanging. The design combines a playful expression with a minimalist aesthetic, perfect for adding character to avatars.",
        },
        {
            assetId = "7315192066",
            name = "kid",
            description = "This character features a cheerful smile and shaggy brown hair. It sports a green T-shirt with white stars and the number \"8\" printed on it, paired with dark pants. Purple sunglasses add a trendy touch, while white sneakers complete the sporty look, giving the character a fun and casual appearance.",
        },
    },
}
```

### data/NPCDatabase.lua

```lua
return {
    npcs = {
        {
            id = "8c9bba8d-4f9a-4748-9e75-1334e48e2e66", 
            displayName = "Diamond", 
            name = "Diamond", 
            assetId = "4446576906", 
            model = "4446576906", 
            modelName = "Diamond", 
            system_prompt = "I'm sharp as a tack both verbally and emotionally and love wit and humour.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(8.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "e43613f0-cc70-4e98-9b61-2a39fecfa443", 
            displayName = "Goldie", 
            name = "Goldie", 
            assetId = "4446576906", 
            model = "4446576906", 
            modelName = "Goldie", 
            system_prompt = "I'm golden and love luxury and wealth, glamour and glitz.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(10.0, 18.0, -12.0), 
            abilities = {
            "chat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "0544b51c-1009-4231-ac6e-053626135ed4", 
            displayName = "Noobster", 
            name = "Noobster", 
            assetId = "4446576906", 
            model = "4446576906", 
            modelName = "Noobster", 
            system_prompt = "I'm clueless but also can learn fast. I keep on moving in random ways.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(6.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat", 
            "trade", 
            "quest", 
            "combat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "3cff63ac-9960-46bb-af7f-88e824d68dbe", 
            displayName = "Oscar", 
            name = "Oscar", 
            assetId = "7315192066", 
            model = "7315192066", 
            modelName = "Oscar", 
            system_prompt = "I am Oscar, twin brother of Pete and I love chasing trouble.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(0.0, 18.0, -6.0), 
            abilities = {
            "chat", 
            "trade", 
            "quest", 
            "combat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "693ec89f-40f1-4321-aef9-5aac428f478b", 
            displayName = "Pete", 
            name = "Pete", 
            assetId = "90229749986361", 
            model = "90229749986361", 
            modelName = "Pete", 
            system_prompt = "I am Pete, the proud owner of Pete’s Merch Stand. I have got a knack for finding the coolest stuff—visors, caps, even those iconic Adidas sweats that everyone seems to want. My stand’s got it all, and I like to keep things interesting. If you look closely, you might spot that curious mask hanging behind the tree. Its been with me for a while, and, well, let’s just say its got its secrets. I love talking about my merch—its not just stuff, it’s part of what makes my stand the best place to visit! I can be chatty at times. Im a little sunburned from all the sports I do.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(-12.5, 18.0, -126.0), 
            abilities = {
            "move", 
            "chat", 
            "initiate_chat", 
            "follow", 
            "unfollow", 
            "run", 
            "jump", 
            "emote", 
        }, 
            shortTermMemory = {}, 
        },
    },
}
```

### client/NPCClientChatHandler.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)

-- Add at the top with other variables
local recentMessages = {}
local MESSAGE_CACHE_TIME = 0.1

-- Add helper function
local function generateMessageId(npcId, message)
    return string.format("%s_%s", npcId, message)
end

-- Modify the chat event handler
local function onNPCChat(npcName, message)
    -- Generate message ID
    local messageId = generateMessageId(npcName, message)
    
    -- Check for duplicate message
    if recentMessages[messageId] then
        if tick() - recentMessages[messageId] < MESSAGE_CACHE_TIME then
            LoggerService:debug("CHAT", "Skipping duplicate message: " .. messageId)
            return -- Skip duplicate message
        end
    end
    
    -- Store message timestamp
    recentMessages[messageId] = tick()
    
    -- Clean up old messages
    for id, timestamp in pairs(recentMessages) do
        if tick() - timestamp > MESSAGE_CACHE_TIME then
            recentMessages[id] = nil
        end
    end
    
    LoggerService:debug("CHAT", string.format("Adding chat message from %s: %s", npcName, message))
    
    -- Add message to chat
    game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
        Text = string.format("[%s]: %s", npcName, message),
        Color = Color3.fromRGB(255, 170, 0)
    })
end

-- Connect event handler
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
NPCChatEvent.OnClientEvent:Connect(onNPCChat)

LoggerService:info("SYSTEM", "NPC Client Chat Handler initialized") 
```

### client/NPCClientHandler.client.lua

```lua
-- NPCClientHandler.client.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextService = game:GetService("TextService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Get the chat specific RemoteEvent
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")
local currentNPCConversation = nil  -- Track which NPC we're talking to

-- Function to safely send a message to the chat system
local function sendToChat(npcName, message)
    -- Try to filter the message (optional but recommended)
    local success, filteredMessage = pcall(function()
        return TextService:FilterStringAsync(message, Players.LocalPlayer.UserId)
    end)
    
    if not success then
        filteredMessage = message -- Use original if filtering fails
    end
    
    -- Format the message with NPC name
    local formattedMessage = string.format("[%s] %s", npcName, filteredMessage)
    
    -- Send using legacy chat system
    if game:GetService("StarterGui"):GetCoreGuiEnabled(Enum.CoreGuiType.Chat) then
        game:GetService("StarterGui"):SetCore("ChatMakeSystemMessage", {
            Text = formattedMessage,
            Color = Color3.fromRGB(249, 217, 55),
            Font = Enum.Font.SourceSansBold
        })
    end
    
    -- Also try TextChatService if available
    local TextChatService = game:GetService("TextChatService")
    if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
        local channel = TextChatService.TextChannels:FindFirstChild("RBXGeneral")
        if channel then
            channel:DisplaySystemMessage(formattedMessage)
        end
    end
end

-- Function to handle player chat messages
local function onPlayerChatted(message)
    -- Check if we're in a conversation with an NPC
    if currentNPCConversation then
        -- Send the message to the server
        NPCChatEvent:FireServer({
            npcName = currentNPCConversation,
            message = message
        })
    end
end

-- Handle incoming NPC chat messages
NPCChatEvent.OnClientEvent:Connect(function(data)
    if not data then return end

    -- Handle different types of messages
    if data.type == "started_conversation" then
        currentNPCConversation = data.npcName
        sendToChat("System", "Started conversation with " .. data.npcName)
    elseif data.type == "ended_conversation" then
        currentNPCConversation = nil
        sendToChat("System", "Ended conversation with " .. data.npcName)
    elseif data.npcName and data.message then
        sendToChat(data.npcName, data.message)
    end
end)

-- Connect to TextChatService for modern chat
local TextChatService = game:GetService("TextChatService")
if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
    TextChatService.SendingMessage:Connect(function(textChatMessage)
        onPlayerChatted(textChatMessage.Text)
    end)
end

-- Connect to legacy chat system
local player = Players.LocalPlayer
if player then
    player.Chatted:Connect(onPlayerChatted)
end

LoggerService:info("SYSTEM", "NPC Client Chat Handler initialized")
```
