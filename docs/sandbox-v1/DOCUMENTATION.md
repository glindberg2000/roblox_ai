# sandbox-v1 Documentation

## Directory Structure

```
├── assets
│   ├── npcs
│   └── unknown
├── client
│   └── NPCClientHandler.client.lua
├── data
│   ├── AssetDatabase.json
│   ├── AssetDatabase.lua
│   ├── NPCDatabase.json
│   ├── NPCDatabase.lua
│   └── PlayerDatabase.json
├── server
│   ├── AssetInitializer.server.lua
│   ├── ChatSetup.lua
│   ├── ChatSetup.server.lua
│   ├── InteractionController.lua
│   ├── Logger.lua
│   ├── MainNPCScript.lua
│   ├── MainNPCScript.server.lua
│   ├── MockPlayer.lua
│   ├── MockPlayerTest.server.lua
│   ├── NPCChatHandler.lua
│   ├── NPCConfigurations.lua
│   ├── NPCInteractionTest.server.lua
│   ├── NPCSystemInitializer.server.lua
│   └── PlayerJoinHandler.server.lua
├── shared
│   ├── NPCSystem
│   │   ├── NPCChatHandler.lua
│   │   └── V4ChatClient.lua
│   ├── AnimationManager.lua
│   ├── AssetModule.lua
│   ├── ChatRouter.lua
│   ├── ChatUtils.lua
│   ├── ConversationManager.lua
│   ├── ConversationManagerV2.lua
│   ├── LettaConfig.lua
│   ├── NPCChatHandler.lua
│   ├── NPCConfig.lua
│   ├── NPCManagerV3.lua
│   ├── V3ChatClient.lua
│   └── V4ChatClient.lua
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

-- Initialize Logger
local Logger = require(ServerScriptService.Logger)

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

```

### server/NPCSystemInitializer.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))

-- Initialize storage structure first
local function ensureStorage()
	-- Create Assets/npcs folder structure
	local Assets = ServerStorage:FindFirstChild("Assets") or 
				   Instance.new("Folder", ServerStorage)
	Assets.Name = "Assets"
	
	local npcs = Assets:FindFirstChild("npcs") or 
				 Instance.new("Folder", Assets)
	npcs.Name = "npcs"
	
	-- Get list of required models from NPCDatabase
	local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
	
	-- Scan the npcs folder for available models
	local availableModels = {}
	for _, model in ipairs(npcs:GetChildren()) do
		availableModels[model.Name] = true
		Logger:log("ASSET", string.format("Found model: %s", model.Name))
	end
	
	-- Check which required models are missing
	for _, npc in ipairs(npcDatabase.npcs) do
		if not availableModels[npc.model] then
			Logger:log("ERROR", string.format("Missing required model '%s' for NPC: %s", 
				npc.model, npc.displayName))
		end
	end
	
	return npcs
end

local npcsFolder = ensureStorage()

-- Initialize events for NPC chat and interaction
if not ReplicatedStorage:FindFirstChild("NPCChatEvent") then
	local NPCChatEvent = Instance.new("RemoteEvent")
	NPCChatEvent.Name = "NPCChatEvent"
	NPCChatEvent.Parent = ReplicatedStorage
	Logger:log("SYSTEM", "Created NPCChatEvent")
end

if not ReplicatedStorage:FindFirstChild("EndInteractionEvent") then
	local EndInteractionEvent = Instance.new("RemoteEvent")
	EndInteractionEvent.Name = "EndInteractionEvent"
	EndInteractionEvent.Parent = ReplicatedStorage
	Logger:log("SYSTEM", "Created EndInteractionEvent")
end

Logger:log("SYSTEM", "NPC System initialized. Using V3 system.")

-- Create and store NPCManager instance
local npcManager = NPCManagerV3.getInstance()
_G.NPCManager = npcManager

```

### server/MainNPCScript.lua

```lua
-- MainNPCScript.lua
function updateNPCs()
    Logger:log("UPDATE", "------- Starting NPC State Update -------")
    
    for _, npc in pairs(NPCManager.npcs) do
        NPCManager:updateNPCState(npc)
    end
    
    Logger:log("UPDATE", "------- Finished NPC State Update -------")
    wait(UPDATE_INTERVAL)
end 
```

### server/ChatSetup.server.lua

```lua
local ChatService = game:GetService("Chat")
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

Logger:log("SYSTEM", "Setting up chat service")

-- Enable bubble chat without checking ChatVersion
ChatService.BubbleChatEnabled = true

Logger:log("SYSTEM", "Chat setup completed")
```

### server/NPCConfigurations.lua

```lua
-- Script Name: NPCConfigurations
-- Script Location: ServerScriptService

return {
	{
		npcId = "eldrin",
		displayName = "Eldrin the Wise",
		model = "Eldrin",
		responseRadius = 20,
		spawnPosition = Vector3.new(0, 5, 0),
	},
	{
		npcId = "luna",
		displayName = "Luna the Stargazer",
		model = "Luna",
		responseRadius = 15,
		spawnPosition = Vector3.new(10, 5, 10),
	},
}

```

### server/NPCChatHandler.lua

```lua
function NPCChatHandler:handleResponse(response, npc, participant)
    -- Check if this is a player interaction
    local participantType = typeof(participant) == "Instance" and participant:IsA("Player") and "player" or "npc"
    
    -- Store conversation history
    npc.chatHistory = npc.chatHistory or {}
    table.insert(npc.chatHistory, {
        message = response.message,
        timestamp = os.time(),
        sender = npc.displayName
    })

    -- Handle player interactions
    if participantType == "player" then
        -- Always prioritize player interactions
        npc.isInteracting = true
        npc.interactingPlayer = participant
        npc.isWindingDown = false
        npc.isEndingConversation = false
        
        -- Remove any end conversation flags
        if response.metadata then
            response.metadata.should_end = nil
        end
        
        -- Force end any NPC conversations
        if npc.currentParticipant and typeof(npc.currentParticipant) ~= "Instance" then
            NPCManagerV3:endInteraction(npc, npc.currentParticipant)
        end
    else
        -- For NPC conversations
        if npc.interactingPlayer then
            -- If talking to a player, don't process NPC chat
            return nil
        end
        
        -- Only allow natural endings for NPC-NPC conversations
        if response.metadata and response.metadata.should_end then
            npc.isWindingDown = true
        end
    end

    -- Include chat history in context
    if not response.context then
        response.context = {}
    end
    response.context.interaction_history = npc.chatHistory

    return response
end 
```

### server/Logger.lua

```lua
-- Logger.lua
local Logger = {
    LogLevel = {
        DEBUG = 1,
        INFO = 2,
        WARN = 3,
        ERROR = 4
    },
    currentLevel = 1,  -- Default to DEBUG
    categoryFilters = {
        -- System & Debug
        SYSTEM = true,
        DEBUG = true,
        ERROR = true,
        
        -- NPC Behavior
        VISION = false,
        MOVEMENT = true,
        ACTION = true,
        ANIMATION = true,
        
        -- Interaction & Chat
        CHAT = true,
        INTERACTION = true,
        RESPONSE = true,
        
        -- State & Data
        STATE = true,
        DATABASE = true,
        ASSET = true,
        API = true,
    }
}

function Logger:log(category, message)
    if self.categoryFilters[category] == false then
        return
    end
    
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    print(string.format("[%s] [%s] %s", timestamp, category:upper(), message))
end

return Logger
```

### server/AssetInitializer.server.lua

```lua
-- AssetInitializer.server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Load the AssetDatabase file directly
local AssetDatabase = require(game:GetService("ServerScriptService").AssetDatabase)

-- Create or get LocalDB in ReplicatedStorage for storing asset descriptions
local LocalDB = ReplicatedStorage:FindFirstChild("LocalDB") or Instance.new("Folder", ReplicatedStorage)
LocalDB.Name = "LocalDB"

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

    print(string.format(
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
print("All assets initialized from local database.")

-- Print out all stored assets for verification
print("Verifying stored assets in LocalDB:")
for _, assetEntry in ipairs(LocalDB:GetChildren()) do
	local nameValue = assetEntry:FindFirstChild("Name")
	local descValue = assetEntry:FindFirstChild("Description")
	local imageValue = assetEntry:FindFirstChild("ImageUrl")

	if nameValue and descValue and imageValue then
		print(
			string.format(
				"Verified asset: ID: %s, Name: %s, Description: %s",
				assetEntry.Name,
				nameValue.Value,
				string.sub(descValue.Value, 1, 50) .. "..."
			)
		)
	else
		print(
			string.format(
				"Error verifying asset: ID: %s, Name exists: %s, Description exists: %s, ImageUrl exists: %s",
				assetEntry.Name,
				tostring(nameValue ~= nil),
				tostring(descValue ~= nil),
				tostring(imageValue ~= nil)
			)
		)
	end
end

-- Function to check a specific asset by name
local function checkAssetByName(assetName)
	local assetId = AssetLookup[assetName]
	if assetId then
		local assetEntry = LocalDB:FindFirstChild(assetId)
		if assetEntry then
			local nameValue = assetEntry:FindFirstChild("Name")
			local descValue = assetEntry:FindFirstChild("Description")
			local imageValue = assetEntry:FindFirstChild("ImageUrl")

			print(string.format("Asset check by name: %s", assetName))
			print("  ID: " .. assetId)
			print("  Name exists: " .. tostring(nameValue ~= nil))
			print("  Description exists: " .. tostring(descValue ~= nil))
			print("  ImageUrl exists: " .. tostring(imageValue ~= nil))

			if nameValue then
				print("  Name value: " .. nameValue.Value)
			end
			if descValue then
				print("  Description value: " .. string.sub(descValue.Value, 1, 50) .. "...")
			end
			if imageValue then
				print("  ImageUrl value: " .. imageValue.Value)
			end
		else
			print("Asset entry not found for name: " .. assetName)
		end
	else
		print("Asset not found in lookup table: " .. assetName)
	end
end

-- Check specific assets by name
checkAssetByName("Tesla Cybertruck")
checkAssetByName("Jeep")
checkAssetByName("Road Sign Stop")
checkAssetByName("HawaiiClothing Store")

print("Asset initialization complete. AssetModule is now available in ReplicatedStorage.")

```

### server/ChatSetup.lua

```lua
local ChatService = game:GetService("Chat")

-- Initialize chat service
local function initializeChat()
    local success, err = pcall(function()
        -- Enable chat bubbles
        ChatService:SetBubbleChatSettings({
            BubbleDuration = 10,
            MaxDistance = 80,
            BackgroundColor3 = Color3.fromRGB(255, 255, 255),
            TextColor3 = Color3.fromRGB(0, 0, 0),
            TextSize = 16
        })
    end)
    
    if not success then
        warn("Failed to initialize chat:", err)
    end
end

return {
    initialize = initializeChat
} 
```

### server/InteractionController.lua

```lua
-- ServerScriptService/InteractionController.lua
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

local InteractionController = {}
InteractionController.__index = InteractionController

function InteractionController.new()
    local self = setmetatable({}, InteractionController)
    self.activeInteractions = {}
    Logger:log("SYSTEM", "InteractionController initialized")
    return self
end

function InteractionController:startInteraction(player, npc)
    if self.activeInteractions[player] then
        Logger:log("PLAYER", string.format("Player %s already in interaction", player.Name))
        return false
    end
    self.activeInteractions[player] = {npc = npc, startTime = tick()}
    Logger:log("PLAYER", string.format("Started interaction: %s with %s", player.Name, npc.displayName))
    return true
end

function InteractionController:endInteraction(player)
    Logger:log("PLAYER", string.format("Ending interaction for player %s", player.Name))
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
    Logger:log("PLAYER", string.format("Started group interaction with %d players", #players))
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

-- Test function to run all checks
local function runTests()
    print("Starting MockPlayer tests...")
    
    -- Test 1: Basic instantiation with type
    local testPlayer = MockPlayer.new("TestUser", 12345, "npc")
    assert(testPlayer ~= nil, "MockPlayer should be created successfully")
    assert(testPlayer.Name == "TestUser", "Name should match constructor argument")
    assert(testPlayer.DisplayName == "TestUser", "DisplayName should match Name")
    assert(testPlayer.UserId == 12345, "UserId should match constructor argument")
    assert(testPlayer.Type == "npc", "Type should be set to npc")
    print("✓ Basic instantiation tests passed")
    
    -- Test 2: Default type behavior
    local defaultPlayer = MockPlayer.new("DefaultUser")
    assert(defaultPlayer.Type == "npc", "Default Type should be 'npc'")
    print("✓ Default type test passed")
    
    -- Test 3: IsA functionality
    assert(testPlayer:IsA("Player") == true, "IsA('Player') should return true")
    print("✓ IsA tests passed")
    
    -- Test 4: GetParticipantType functionality
    assert(testPlayer:GetParticipantType() == "npc", "GetParticipantType should return 'npc'")
    local playerTypeMock = MockPlayer.new("PlayerTest", 789, "player")
    assert(playerTypeMock:GetParticipantType() == "player", "GetParticipantType should return 'player'")
    print("✓ GetParticipantType tests passed")
    
    print("All MockPlayer tests passed successfully!")
end

-- Run tests in protected call to catch any errors
local success, error = pcall(runTests)
if not success then
    warn("MockPlayer tests failed: " .. tostring(error))
end 
```

### server/NPCInteractionTest.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local NPCManagerV3 = require(ReplicatedStorage.NPCManagerV3)

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

### server/MockPlayer.lua

```lua
-- ServerScriptService/MockPlayer.lua
local MockPlayer = {}
MockPlayer.__index = MockPlayer

function MockPlayer.new(name, userId, participantType)
    local self = setmetatable({}, MockPlayer)
    self.Name = name
    self.DisplayName = name
    self.UserId = userId or -1  -- Keep negative ID for backwards compatibility
    self.Type = participantType or "npc"  -- Default to "npc" if not specified
    return self
end

function MockPlayer:IsA(className)
    return className == "Player"
end

-- Add helper method to check participant type
function MockPlayer:GetParticipantType()
    return self.Type
end

return MockPlayer
```

### shared/V3ChatClient.lua

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

### shared/V4ChatClient.lua

```lua
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

### shared/NPCChatHandler.lua

```lua
-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.NPCSystem.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.NPCSystem.V3ChatClient)
local HttpService = game:GetService("HttpService")

function NPCChatHandler:HandleChat(request)
    print("NPCChatHandler: Received request", HttpService:JSONEncode(request))
    
    -- Try V4 first
    print("NPCChatHandler: Attempting V4")
    local v4Response = V4ChatClient:SendMessage(request)
    
    if v4Response then
        print("NPCChatHandler: V4 succeeded", HttpService:JSONEncode(v4Response))
        -- Ensure we have a valid message
        if not v4Response.message then
            v4Response.message = "I'm having trouble understanding right now."
        end
        return v4Response
    end
    
    -- If V4 failed, return error response
    print("NPCChatHandler: V4 failed, returning error response")
    return {
        message = "I'm having trouble understanding right now.",
        action = { type = "none" },
        metadata = {}
    }
end

return NPCChatHandler 
```

### shared/ChatUtils.lua

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

### shared/NPCManagerV3.lua

```lua
-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local ChatService = game:GetService("Chat")

local AnimationManager = require(ReplicatedStorage.Shared.AnimationManager)
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local NPCChatHandler = require(ReplicatedStorage.NPCSystem.NPCChatHandler)

-- Initialize Logger
local Logger
local function initializeLogger()
    local success, result = pcall(function()
        if game:GetService("RunService"):IsServer() then
            return require(ServerScriptService:WaitForChild("Logger"))
        else
            return require(ReplicatedStorage:WaitForChild("Logger"))
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
Logger:log("SYSTEM", "NPCManagerV3 module loaded")

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
    
    Logger:log("SYSTEM", "Thread manager initialized")
end

function NPCManagerV3.getInstance()
    if not instance then
        instance = setmetatable({}, NPCManagerV3)
        instance.npcs = {}
        instance.responseCache = {}
        instance.interactionController = require(game.ServerScriptService.InteractionController).new()
        instance.activeInteractions = {} -- Track ongoing interactions
        instance.movementStates = {} -- Track movement states per NPC
        instance.activeConversations = {}  -- Track active conversations
        instance.lastInteractionTime = {}  -- Track timing
        instance.conversationCooldowns = {} -- Track cooldowns between NPCs
        
        -- Add thread manager initialization
        instance:initializeThreadManager()
        
        -- Initialize immediately
        Logger:log("SYSTEM", "Initializing NPCManagerV3")
        instance:loadNPCDatabase()
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
    
    Logger:log("CHAT", string.format("Received message from player %s to NPC %s: %s",
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
                Logger:log("INTERACTION", string.format("NPC %s is not interacting with player %s", 
                    npc.displayName, 
                    player.Name
                ))
            end
            return
        end
    end
    
    Logger:log("ERROR", string.format("NPC %s not found when handling player message", npcName))
end

function NPCManagerV3:loadNPCDatabase()
    if self.databaseLoaded then
        Logger:log("DATABASE", "Database already loaded, skipping...")
        return
    end
    
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    Logger:log("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
    for _, npcData in ipairs(npcDatabase.npcs) do
        self:createNPC(npcData)
    end
    
    self.databaseLoaded = true
    Logger:log("DATABASE", "NPC Database loaded successfully")
end

function NPCManagerV3:createNPC(npcData)
    Logger:log("NPC", string.format("Creating NPC: %s", npcData.displayName))
    
    -- Debug log NPC data
    Logger:log("DEBUG", string.format("Creating NPC with data: %s", 
        HttpService:JSONEncode({
            displayName = npcData.displayName,
            abilities = npcData.abilities
        })
    ))

    if not workspace:FindFirstChild("NPCs") then
        Instance.new("Folder", workspace).Name = "NPCs"
        Logger:log("SYSTEM", "Created NPCs folder in workspace")
    end

    local model = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
    if not model then
        Logger:log("ERROR", string.format("Model not found for NPC: %s", npcData.displayName))
        return
    end

    local npcModel = model:Clone()
    npcModel.Name = npcData.displayName
    npcModel.Parent = workspace.NPCs

    -- Check for necessary parts
    local humanoidRootPart = npcModel:FindFirstChild("HumanoidRootPart")
    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    local head = npcModel:FindFirstChild("Head")

    if not humanoidRootPart or not humanoid or not head then
        Logger:log("ERROR", string.format("NPC model %s is missing essential parts. Skipping creation.", npcData.displayName))
        npcModel:Destroy()
        return
    end

    -- Ensure the model has a PrimaryPart
    npcModel.PrimaryPart = humanoidRootPart

    -- Apply animations
    AnimationManager:applyAnimations(humanoid)

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

    -- Position the NPC
    humanoidRootPart.CFrame = CFrame.new(npcData.spawnPosition)

    self:setupClickDetector(npc)
    self.npcs[npc.id] = npc
    
    Logger:log("NPC", string.format("NPC added: %s (Total NPCs: %d)", npc.displayName, self:getNPCCount()))
    
    -- Return the created NPC
    return npc
end

-- Add a separate function to test chat for all NPCs
function NPCManagerV3:testAllNPCChat()
    Logger:log("TEST", "Testing chat for all NPCs...")
    for _, npc in pairs(self.npcs) do
        if npc.model and npc.model:FindFirstChild("Head") then
            -- Try simple chat method only
            game:GetService("Chat"):Chat(npc.model.Head, "Test chat from " .. npc.displayName)
            wait(0.5) -- Small delay between tests
        end
    end
    Logger:log("TEST", "Chat testing complete")
end

-- Modify the createNPC function to initialize chat speaker
-- Store the original createNPC function
local originalCreateNPC = NPCManagerV3.createNPC

-- Override createNPC to add chat speaker initialization
function NPCManagerV3:createNPC(npcData)
    local npc = originalCreateNPC(self, npcData)
    if npc then
        self:initializeNPCChatSpeaker(npc)
    end
    return npc
end

function NPCManagerV3:getNPCCount()
	local count = 0
	for _ in pairs(self.npcs) do
		count = count + 1
	end
	Logger:log("DEBUG", string.format("Current NPC count: %d", count))
	return count
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius

	-- Try to parent to HumanoidRootPart, if not available, use any BasePart
	local parent = npc.model:FindFirstChild("HumanoidRootPart") or npc.model:FindFirstChildWhichIsA("BasePart")

	if parent then
		clickDetector.Parent = parent
		Logger:log("INTERACTION", string.format("Set up ClickDetector for %s with radius %d", 
			npc.displayName, 
			npc.responseRadius
		))
	else
		Logger:log("ERROR", string.format("Could not find suitable part for ClickDetector on %s", npc.displayName))
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



function NPCManagerV3:endInteraction(npc, participant, interactionId)
    Logger:log("INTERACTION", string.format("Pausing interaction for %s with %s (ID: %s)",
        npc.displayName,
        participant and participant.Name or "Unknown",
        interactionId or "N/A"
    ))

    -- Update timestamps
    npc.lastInteractionTime = tick()
    npc.lastConversationTime = tick()
    
    if participant then
        npc.lastInteractionPartner = typeof(participant) == "Instance" and participant.UserId or participant.npcId
    end

    -- Preserve conversation context and history
    if npc.currentConversationId then
        Logger:log("CHAT", string.format("Preserving conversation %s for %s with %s",
            npc.currentConversationId,
            npc.displayName,
            participant.Name or participant.displayName
        ))
    end

    -- Clean up interaction tracking
    if interactionId then
        self.activeInteractions[interactionId] = nil
    end

    -- Free movement state but preserve conversation data
    self:setNPCMovementState(npc, "free")
    npc.isInteracting = false
    npc.interactingPlayer = nil

    -- Handle NPC-to-NPC cleanup
    if self:isNPCParticipant(participant) then
        local otherNPC = self.npcs[participant.npcId]
        if otherNPC then
            self:setNPCMovementState(otherNPC, "free")
            otherNPC.isInteracting = false
            otherNPC.interactingPlayer = nil
        end
    end

    -- Notify client of paused conversation
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        NPCChatEvent:FireClient(participant, {
            npcName = npc.displayName,
            type = "paused_conversation",
            conversationId = npc.currentConversationId
        })
    end
end

function NPCManagerV3:getCacheKey(npc, player, message)
	local context = {
		npcId = npc.id,
		
		playerId = player.UserId,
		message = message,
		memory = npc.shortTermMemory[player.UserId],
	}
	
	local key = HttpService:JSONEncode(context)
	Logger:log("DEBUG", string.format("Generated cache key for %s and %s", npc.displayName, player.Name))
	return key
end

-- Require the Asset Database
local AssetDatabase = require(game.ServerScriptService.AssetDatabase)

-- Function to lookup asset data by name
local function getAssetData(assetName)
	for _, asset in ipairs(AssetDatabase.assets) do
		if asset.name == assetName then
			return asset
		end
	end
	return nil -- Return nil if the asset is not found
end

function NPCManagerV3:updateNPCVision(npc)
    npc.visibleEntities = {}
    local npcPosition = npc.model.PrimaryPart.Position

    -- First detect other NPCs
    for id, otherNPC in pairs(self.npcs) do
        if otherNPC ~= npc and otherNPC.model and otherNPC.model.PrimaryPart then
            local distance = (otherNPC.model.PrimaryPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "npc",
                    instance = otherNPC,
                    distance = distance,
                    name = otherNPC.displayName
                })
                Logger:log("VISION", string.format("%s sees NPC: %s at distance: %.2f",
                    npc.displayName,
                    otherNPC.displayName,
                    distance
                ))
            end
        end
    end

    -- Then detect players
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "player",
                    instance = player,
                    distance = distance,
                    name = player.Name
                })
                Logger:log("VISION", string.format("%s sees player: %s at distance: %.2f",
                    npc.displayName,
                    player.Name,
                    distance
                ))
            end
        end
    end
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
        Logger:log("CHAT", "Blocking error message propagation between NPCs")
        return
    end

    -- Ensure we have a valid model and head
    if not npc.model or not npc.model:FindFirstChild("Head") then
        Logger:log("ERROR", string.format("Cannot display message for %s - missing model or head", npc.displayName))
        return
    end

    -- Create chat bubble
    local success, err = pcall(function()
        game:GetService("Chat"):Chat(npc.model.Head, message)
        Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
    end)
    if not success then
        Logger:log("ERROR", string.format("Failed to create chat bubble: %s", err))
    end

    -- Handle NPC-to-NPC messages
    if self:isNPCParticipant(recipient) then
        Logger:log("CHAT", string.format("NPC %s to NPC %s: %s",
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
        Logger:log("CHAT", string.format("NPC %s sending message to player %s: %s",
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
    if response.metadata and response.metadata.should_end then
        -- Set cooldown
        local cooldownKey = npc.id .. "_" .. participant.UserId
        self.conversationCooldowns[cooldownKey] = os.time()
        
        -- Unlock movement
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
            npc.isMovementLocked = false
        end
    end

    if response.message then
        self:displayMessage(npc, response.message, participant)
    end

    if response.action then
        Logger:log("ACTION", string.format("Executing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.action)
        ))
        self:executeAction(npc, participant, response.action)
    end

    if response.internal_state then
        Logger:log("STATE", string.format("Updating internal state for %s: %s",
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
            Logger:log("SYSTEM", string.format("Initialized chat speaker for NPC: %s", npc.displayName))
        end
    end
end

-- Update the displayNPCToNPCMessage function in NPCManagerV3.lua
function NPCManagerV3:testChatBubbles(fromNPC)
    if not fromNPC or not fromNPC.model then
        Logger:log("ERROR", "Invalid NPC for chat test")
        return
    end

    local head = fromNPC.model:FindFirstChild("Head")
    if not head then
        Logger:log("ERROR", string.format("NPC %s has no Head part!", fromNPC.displayName))
        return
    end

    -- Try each chat method
    Logger:log("TEST", "Testing chat methods...")

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
        Logger:log("ERROR", "ChatService method failed: " .. tostring(err))
    end

    Logger:log("TEST", "Chat test complete")
end

-- Also update displayNPCToNPCMessage to try all methods
function NPCManagerV3:displayNPCToNPCMessage(fromNPC, toNPC, message)
    if not (fromNPC and toNPC and message) then
        Logger:log("ERROR", "Missing required parameters for NPC-to-NPC message")
        return
    end

    Logger:log("CHAT", string.format("NPC %s to NPC %s: %s", 
        fromNPC.displayName or "Unknown",
        toNPC.displayName or "Unknown",
        message
    ))
    
    -- Use the same direct Chat call that worked in our test
    if fromNPC.model and fromNPC.model:FindFirstChild("Head") then
        game:GetService("Chat"):Chat(fromNPC.model.Head, message)
        Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", fromNPC.displayName))
    end
    
    -- Fire event to all clients for redundancy
    NPCChatEvent:FireAllClients({
        npcName = fromNPC.displayName,
        message = message,
        type = "npc_chat"
    })
end

function NPCManagerV3:executeAction(npc, player, action)
    Logger:log("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    if action.type == "stop_talking" then
        -- Stop following if we were following this player
        if npc.isFollowing and npc.followTarget == player then
            Logger:log("MOVEMENT", string.format("Stopping follow as part of ending interaction: %s", player.Name))
            self:stopFollowing(npc)
        end
        -- Let the normal conversation flow handle the ending
    elseif action.type == "follow" then
        Logger:log("MOVEMENT", string.format("Starting to follow player: %s", player.Name))
        self:startFollowing(npc, player)
    elseif action.type == "unfollow" then
        Logger:log("MOVEMENT", string.format("Stopping following player: %s", player.Name))
        self:stopFollowing(npc)
    elseif action.type == "emote" and action.data and action.data.emote then
        Logger:log("ANIMATION", string.format("Playing emote: %s", action.data.emote))
        self:playEmote(npc, action.data.emote)
    elseif action.type == "move" and action.data and action.data.position then
        Logger:log("MOVEMENT", string.format("Moving to position: %s", 
            tostring(action.data.position)
        ))
        self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
    elseif action.type == "none" then
        Logger:log("ACTION", "No action required")
    else
        Logger:log("ERROR", string.format("Unknown action type: %s", action.type))
    end
end

function NPCManagerV3:startFollowing(npc, player)
    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()
    npc.isWalking = false  -- Will be set to true when movement starts
    -- Ensure NPC can move while following
    self:setNPCMovementState(npc, "following")
    Logger:log("STATE", string.format("Follow state set for %s: isFollowing=%s, followTarget=%s",
        npc.displayName,
        tostring(npc.isFollowing),
        tostring(player.Name)
    ))
end

function NPCManagerV3:updateInternalState(npc, internalState)
	Logger:log("STATE", string.format("Updating internal state for %s: %s",
		npc.displayName,
		HttpService:JSONEncode(internalState)
	))
	
	for key, value in pairs(internalState) do
		npc[key] = value
	end
end

function NPCManagerV3:playEmote(npc, emoteName)
    local Animator = npc.model:FindFirstChildOfClass("Animator")
    if Animator then
        local animation = ServerStorage.Animations:FindFirstChild(emoteName)
        if animation then
            Animator:LoadAnimation(animation):Play()
            Logger:log("ANIMATION", string.format("Playing emote %s for %s", emoteName, npc.displayName))
        else
            Logger:log("ERROR", string.format("Animation not found: %s", emoteName))
        end
    end
end

function NPCManagerV3:moveNPC(npc, targetPosition)
    Logger:log("MOVEMENT", string.format("Moving %s to position %s", 
        npc.displayName, 
        tostring(targetPosition)
    ))
    
    local Humanoid = npc.model:FindFirstChildOfClass("Humanoid")
    if Humanoid then
        Humanoid:MoveTo(targetPosition)
    else
        Logger:log("ERROR", string.format("Cannot move %s (no Humanoid)", npc.displayName))
    end
end

function NPCManagerV3:stopFollowing(npc)
    npc.isFollowing = false
    npc.followTarget = nil
    npc.followStartTime = nil

    -- Stop movement and animations
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        humanoid:MoveTo(npc.model.PrimaryPart.Position)
        AnimationManager:stopAnimations(humanoid)
    end

    Logger:log("MOVEMENT", string.format("%s stopped following and movement halted", npc.displayName))
end

function NPCManagerV3:handleNPCInteraction(npc, participant, message)
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

    Logger:log("DEBUG", string.format(
        "Starting interaction - NPC: %s, Participant: %s (%s), Message: %s",
        npc.displayName,
        participantName,
        participantType,
        message
    ))

    -- Generate unique interaction ID
    local interactionId = HttpService:GenerateGUID()
    
    -- Check if we can create new interaction thread
    if #self.threadPool.interactionThreads >= self.threadLimits.interaction then
        Logger:log("THREAD", "Maximum interaction threads reached, queuing interaction")
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
            Logger:log("CHAT", string.format(
                "Interaction between %s and %s is on cooldown",
                npc.displayName,
                participant.Name
            ))
            return
        end

        -- Lock movement at start of interaction
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            npc.model.Humanoid.WalkSpeed = 0
            npc.isMovementLocked = true
            Logger:log("MOVEMENT", string.format("Locked movement for %s during interaction", npc.displayName))
        end

        -- Check for conversation ending phrases
        local endPhrases = {
            "gotta run",
            "goodbye",
            "see you later",
            "bye",
            "talk to you later"
        }
        
        for _, phrase in ipairs(endPhrases) do
            if string.lower(message):find(phrase) then
                -- Set cooldown
                self.conversationCooldowns[cooldownKey] = os.time()
                
                -- Send goodbye response
                self:displayMessage(npc, "Goodbye! Talk to you later!", participant)
                
                -- Unlock movement
                if npc.model and npc.model:FindFirstChild("Humanoid") then
                    npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
                    npc.isMovementLocked = false
                end
                
                return nil
            end
        end

        local response = NPCChatHandler:HandleChat({
            message = message,
            npc_id = npc.id,
            participant_id = participant.UserId,
            context = {
                participant_type = "npc",
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
                Logger:log("MOVEMENT", string.format("Unlocked movement for %s after failed interaction", npc.displayName))
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
                Logger:log("THREAD", string.format("Terminated hung interaction thread %s", interactionId))
            end
        end)
        
        if not success then
            Logger:log("ERROR", string.format("Thread monitoring failed: %s", result))
        end
    end)
end

function NPCManagerV3:canNPCsInteract(npc1, npc2)
    -- Check if either NPC is in conversation
    for userId, activeNPC in pairs(self.activeConversations) do
        if activeNPC == npc1 or activeNPC == npc2 then
            Logger:log("CHAT", string.format(
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
    
    -- Handle state-specific logic
    if state == "idle" then
        self:stopFollowing(npc)
    elseif state == "following" then
        npc.isFollowing = true
        npc.followTarget = data.target
        npc.followStartTime = os.time()
    end
    
    Logger:log("MOVEMENT", string.format(
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
                Logger:log("THREAD", string.format("Cleaned up inactive %s thread %s", threadType, threadId))
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

return NPCManagerV3

```

### shared/NPCConfig.lua

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

### shared/LettaConfig.lua

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

### shared/AnimationManager.lua

```lua
local AnimationManager = {}
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

local animations = {
    walk = "rbxassetid://180426354", -- Replace with your walk animation asset ID
    jump = "rbxassetid://125750702", -- Replace with your jump animation asset ID
    idle = "rbxassetid://507766388", -- Replace with your idle animation asset ID
}

-- Table to store animations per humanoid
local animationTracks = {}

-- Apply animations to NPC's humanoid
function AnimationManager:applyAnimations(humanoid)
    if not humanoid then
        Logger:log("ERROR", "Cannot apply animations: Humanoid is nil")
        return
    end

    local animator = humanoid:FindFirstChild("Animator") or Instance.new("Animator", humanoid)

    -- Initialize animationTracks for this humanoid
    animationTracks[humanoid] = {}

    -- Preload animations
    for name, id in pairs(animations) do
        local animation = Instance.new("Animation")
        animation.AnimationId = id

        local animationTrack = animator:LoadAnimation(animation)
        animationTracks[humanoid][name] = animationTrack
        Logger:log("ANIMATION", string.format("Loaded animation '%s' for humanoid: %s", 
            name, 
            humanoid.Parent.Name
        ))
    end

    Logger:log("ANIMATION", string.format("Animations applied to humanoid: %s", humanoid.Parent.Name))
end

-- Play a specific animation
function AnimationManager:playAnimation(humanoid, animationName)
    if animationTracks[humanoid] and animationTracks[humanoid][animationName] then
        Logger:log("ANIMATION", string.format("Playing animation '%s' for humanoid: %s", 
            animationName, 
            humanoid.Parent.Name
        ))
        animationTracks[humanoid][animationName]:Play()
    else
        Logger:log("ERROR", string.format("No animation track found: %s for humanoid: %s", 
            animationName, 
            humanoid and humanoid.Parent and humanoid.Parent.Name or "unknown"
        ))
    end
end

-- Stop all animations
function AnimationManager:stopAnimations(humanoid)
    if animationTracks[humanoid] then
        for name, track in pairs(animationTracks[humanoid]) do
            track:Stop()
            Logger:log("ANIMATION", string.format("Stopped animation '%s' for humanoid: %s", 
                name, 
                humanoid.Parent.Name
            ))
        end
    end
end

return AnimationManager
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

### shared/NPCSystem/V4ChatClient.lua

```lua
local V4ChatClient = {}

-- Update SendMessage signature to include participant
function V4ChatClient:SendMessage(npcId, message, participant, context)
    Logger:log("DEBUG", "V4ChatClient:SendMessage called")
    
    -- Try Letta chat first
    local response = self:handleLettaChat(npcId, message, participant, context)
    if response then
        return response
    end
    
    -- If Letta fails, try fallback
    return self:handleFallbackChat(npcId, message, participant, context)
end

-- Update handleLettaChat to handle NPC participants
function V4ChatClient:handleLettaChat(npcId, message, participant, context)
    Logger:log("DEBUG", "Attempting Letta chat first...")
    
    -- Log raw incoming data
    Logger:log("DEBUG", string.format("Raw incoming data: %s", HttpService:JSONEncode({
        message = message,
        npc_id = npcId,
        context = context
    })))
    
    -- Determine participant type and ID
    local participantType = "player"
    local participantId = participant.UserId
    local participantName = participant.Name
    
    if typeof(participant) ~= "Instance" or not participant:IsA("Player") then
        participantType = "npc"
        participantId = participant.id
        participantName = participant.displayName
    end
    Logger:log("DEBUG", string.format("Determined participant type: %s", participantType))
    
    -- Build request data
    local requestData = {
        message = message,
        npc_id = npcId,
        participant_type = participantType,
        participant_id = participantId,
        context = {
            participant_name = participantName,
            interaction_history = context.interaction_history or {},
            participant_type = participantType,
            is_new_conversation = context.is_new_conversation or false,
            npc_location = context.npc_location or "Unknown",
            nearby_players = context.nearby_players or {}
        }
    }
end 
```

### shared/NPCSystem/NPCChatHandler.lua

```lua
local function HandleChat(npcId, message, participant, context)
    Logger:log("DEBUG", string.format("NPCChatHandler: Received request %s", 
        HttpService:JSONEncode({
            message = message,
            npc_id = npcId,
            context = context
        })
    ))

    -- Try V4 first
    Logger:log("DEBUG", "NPCChatHandler: Attempting V4")
    local success, response = pcall(function()
        return V4ChatClient:SendMessage(npcId, message, participant, context)
    end)

    if success and response then
        Logger:log("DEBUG", string.format("NPCChatHandler: V4 succeeded %s", 
            HttpService:JSONEncode(response)
        ))
        return response
    end

    -- If V4 fails, try V3
    Logger:log("DEBUG", "NPCChatHandler: V4 failed, attempting V3")
    success, response = pcall(function()
        return V3ChatClient:SendMessage(npcId, message, participant, context)
    end)

    if success and response then
        Logger:log("DEBUG", "NPCChatHandler: V3 succeeded")
        return response
    end

    -- If both fail, return error
    Logger:log("ERROR", "NPCChatHandler: All chat attempts failed")
    return {
        message = "Sorry, I'm having trouble understanding right now.",
        action = { type = "none" }
    }
end 
```

### data/AssetDatabase.lua

```lua
return {
    assets = {
        {
            assetId = "4446576906",
            name = "Noob2",
            description = "The humanoid asset features a simple, blocky character design. It has a round, yellow head with a cheerful smile, and a blue short-sleeved shirt. The arms are wide and yellow, while the legs are green, creating a bright, colorful appearance. The character embodies a playful, cartoonish style typical of Roblox avatars.",
        },
        {
            assetId = "128282678684676",
            name = "Pete",
            description = "The Roblox character features a bright yellow face with a large, smiling expression. It has spiky blonde hair and wears stylish purple sunglasses. The shirt is black with a prominent smiley face graphic, while the pants are black with a white stripe, giving it a trendy look. The character stands confidently, showcasing its playful design.",
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
            system_prompt = "I'm sharp as a tack both verbally and emotionally.", 
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
            "initiate_chat",
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
            "initiate_chat",
        }, 
            shortTermMemory = {}, 
        },        {
            id = "b11fbfb5-5f46-40cb-9c4c-84ca72b55ac7", 
            displayName = "Pete", 
            name = "Pete", 
            assetId = "7315192066", 
            model = "7315192066", 
            modelName = "Pete", 
            system_prompt = "I sell awesome merch and love to chat about it. My boss, Valterpoop—better known as KrushKen—expects me to keep an eye out for him and his dad, GreggytheEgg, just in case they drop by. Let me know if you’re interested in our products or have any questions; I’m always happy to help!", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(12.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat"
        }, 
            shortTermMemory = {}, 
        },        {
            id = "9db3e3e8-78ff-405b-a11b-240c4afc251e", 
            displayName = "Pete", 
            name = "Pete", 
            assetId = "128282678684676", 
            model = "128282678684676", 
            modelName = "Pete", 
            system_prompt = "A young boy who is curious and always discovering new things.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(10.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat"
        }, 
            shortTermMemory = {}, 
        },
    },
}
```

### client/NPCClientHandler.client.lua

```lua
-- NPCClientHandler.client.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextService = game:GetService("TextService")

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

print("NPC Client Chat Handler initialized")
```
