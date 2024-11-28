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
│   ├── ChatSetup.server.lua
│   ├── InteractionController.lua
│   ├── Logger.lua
│   ├── MainNPCScript.lua
│   ├── MainNPCScript.server.lua
│   ├── MockPlayer.lua
│   ├── MockPlayerTest.server.lua
│   ├── NPCConfigurations.lua
│   ├── NPCInteractionTest.lua
│   ├── NPCInteractionTest.lua```
│   ├── NPCInteractionTest.server.lua
│   ├── NPCSystemInitializer.server.lua
│   └── PlayerJoinHandler.server.lua
└── shared
    ├── AnimationManager.lua
    ├── AssetModule.lua
    ├── ConversationManagerV2.lua
    ├── NPCManagerV3.lua
    └── NPCManagerV3.lua```
```

## Source Files

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

for npcId, npcData in pairs(npcManagerV3.npcs) do
	Logger:log("STATE", string.format("NPC spawned: %s", npcData.displayName))
end

local interactionController = npcManagerV3.interactionController

Logger:log("SYSTEM", "NPC system V3 initialized")

local function checkPlayerProximity()
	for _, player in ipairs(Players:GetPlayers()) do
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if playerPosition then
			for _, npc in pairs(npcManagerV3.npcs) do
				if npc.model and npc.model.PrimaryPart then
					local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
					if distance <= npc.responseRadius and not npc.isInteracting then
						if interactionController:canInteract(player) then
							Logger:log("INTERACTION", string.format("Auto-interaction triggered for %s with %s", 
								npc.displayName, player.Name))
							npcManagerV3:handleNPCInteraction(npc, player, "Hello")
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
			if distance <= npc.responseRadius and distance < closestDistance then
				closestNPC, closestDistance = npc, distance
			end
		end
	end

	if closestNPC then
		Logger:log("INTERACTION", string.format("Routing chat from %s to NPC %s", 
			player.Name, closestNPC.displayName))
		npcManagerV3:handleNPCInteraction(closestNPC, player, message)
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

local function updateNPCs()
	Logger:log("SYSTEM", "Starting NPC update loop")
	while true do
		checkPlayerProximity()
		for _, npc in pairs(npcManagerV3.npcs) do
			npcManagerV3:updateNPCState(npc)
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

-- Create and store NPCManager instance (it will return the same instance if already created)
local npcManager = NPCManagerV3.new()
_G.NPCManager = npcManager

```

### server/NPCInteractionTest.lua

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

### server/MainNPCScript.lua

```lua
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

### server/Logger.lua

```lua
-- Logger.lua
local Logger = {}

-- Define log levels
Logger.LogLevel = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4,
    NONE = 5
}

-- Current log level - can be changed at runtime
Logger.currentLevel = Logger.LogLevel.DEBUG

-- Category filters - Uncomment to disable specific categories
Logger.categoryFilters = {
    -- System & Debug
    -- SYSTEM = false,    -- System-level messages
    -- DEBUG = false,     -- Debug information
    -- ERROR = false,     -- Error messages
    
    -- NPC Behavior
    -- VISION = false,    -- NPC vision updates
    -- MOVEMENT = false,  -- NPC movement
    -- ACTION = false,    -- NPC actions
    -- ANIMATION = false, -- NPC animations
    
    -- Interaction & Chat
    -- CHAT = false,      -- Chat messages
    -- INTERACTION = false, -- Player-NPC interactions
    -- RESPONSE = false,  -- AI responses
    
    -- State & Data
    -- STATE = false,     -- State changes
    -- DATABASE = false,  -- Database operations
    -- ASSET = false,     -- Asset loading/management
    -- API = false,       -- API calls
}

function Logger:setLogLevel(level)
    if self.LogLevel[level] then
        self.currentLevel = self.LogLevel[level]
    end
end

function Logger:enableCategory(category)
    self.categoryFilters[category] = true
    print(string.format("Enabled logging for category: %s", category))
end

function Logger:disableCategory(category)
    self.categoryFilters[category] = false
    print(string.format("Disabled logging for category: %s", category))
end

function Logger:log(category, message, ...)
    -- Check if category is explicitly disabled
    if self.categoryFilters[category] == false then
        return
    end
    
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    
    -- Handle old-style logging (single message parameter)
    if message == nil then
        -- If only one parameter was passed, treat it as the message
        print(string.format("[%s] %s", timestamp, category))
        return
    end
    
    -- Handle new-style logging (category + message)
    print(string.format("[%s] [%s] %s", timestamp, category:upper(), message))
end

-- Convenience methods for each category
function Logger:vision(message)
    self:log("VISION", message)
end

function Logger:movement(message)
    self:log("MOVEMENT", message)
end

function Logger:interaction(message)
    self:log("INTERACTION", message)
end

function Logger:database(message)
    self:log("DATABASE", message)
end

function Logger:asset(message)
    self:log("ASSET", message)
end

function Logger:api(message)
    self:log("API", message)
end

function Logger:state(message)
    self:log("STATE", message)
end

function Logger:animation(message)
    self:log("ANIMATION", message)
end

function Logger:error(message)
    self:log("ERROR", message)
end

function Logger:debug(message)
    self:log("DEBUG", message)
end

-- Example usage:
-- To disable vision logs, uncomment this line:
Logger.categoryFilters.VISION = false
Logger.categoryFilters.MOVEMENT = false
Logger.categoryFilters.ANIMATION = false
-- To re-enable vision logs, uncomment this line:
-- Logger.categoryFilters.VISION = true

-- You can also use these functions in your code:
-- Logger:disableCategory("VISION")
-- Logger:enableCategory("VISION")

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

function NPCManagerV3.getInstance()
    if not instance then
        instance = setmetatable({}, NPCManagerV3)
        instance.npcs = {}
        instance.responseCache = {}
        instance.interactionController = require(game.ServerScriptService.InteractionController).new()
        instance.activeInteractions = {} -- Track ongoing interactions
        instance.movementStates = {} -- Track movement states per NPC
        Logger:log("SYSTEM", "Initializing NPCManagerV3")
        instance:loadNPCDatabase()
    end
    return instance
end

-- Replace .new() with getInstance()
function NPCManagerV3.new()
    return NPCManagerV3.getInstance()
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

function NPCManagerV3:loadNPCDatabase()
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    Logger:log("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
    for _, npcData in ipairs(npcDatabase.npcs) do
        self:createNPC(npcData)
    end
end

function NPCManagerV3:createNPC(npcData)
    Logger:log("NPC", string.format("Creating NPC: %s", npcData.displayName))
    
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

-- Update loadNPCDatabase to run chat test after all NPCs are created
function NPCManagerV3:loadNPCDatabase()
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    Logger:log("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
    for _, npcData in ipairs(npcDatabase.npcs) do
        self:createNPC(npcData)
    end
    
    -- Test chat after all NPCs are created
    wait(1) -- Give a moment for everything to settle
    self:testAllNPCChat()
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
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end



function NPCManagerV3:endInteraction(npc, participant)
    -- First unlock the initiating NPC
    self:unlockNPC(npc)
    
    -- Then unlock the target NPC if this was NPC-to-NPC
    if self:isNPCParticipant(participant) then
        local targetNPC = self.npcs[participant.npcId]
        if targetNPC then
            self:unlockNPC(targetNPC)
        end
    end

    -- Clear states
    npc.isInteracting = false
    npc.interactingPlayer = nil

    self.interactionController:endInteraction(participant)
    
    Logger:log("INTERACTION", string.format("Interaction ended between %s and %s", 
        npc.displayName, 
        participant.Name
    ))
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
    if not participant then return false end
    
    -- Check if it's a mock NPC participant
    if participant.npcId then return true end
    
    -- Check if it's a Player instance
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return false
    end
    
    -- For any other case, check for NPC-specific properties
    return participant.GetParticipantType and participant:GetParticipantType() == "npc"
end

function NPCManagerV3:displayMessage(npc, message, recipient)
    -- Handle player messages
    if typeof(recipient) == "Instance" and recipient:IsA("Player") then
        Logger:log("CHAT", string.format("NPC %s sending message to player %s: %s",
            npc.displayName,
            recipient.Name,
            message
        ))
        
        -- Create chat bubble
        if npc.model and npc.model:FindFirstChild("Head") then
            game:GetService("Chat"):Chat(npc.model.Head, message)
            Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
        end
        
        -- Send to player's chat window
        NPCChatEvent:FireClient(recipient, {
            npcName = npc.displayName,
            message = message,
            type = "chat"
        })
        
        -- Record in chat history
        table.insert(npc.chatHistory, {
            sender = npc.displayName,
            recipient = recipient.Name,
            message = message,
            timestamp = os.time()
        })
        return
    end
    
    -- Handle NPC-to-NPC messages
    if self:isNPCParticipant(recipient) then
        Logger:log("CHAT", string.format("NPC %s to NPC %s: %s",
            npc.displayName,
            recipient.displayName or recipient.Name,
            message
        ))
        
        -- Create chat bubble
        if npc.model and npc.model:FindFirstChild("Head") then
            game:GetService("Chat"):Chat(npc.model.Head, message)
            Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
        end
        
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
    
    -- Log if recipient type is unknown
    Logger:log("ERROR", string.format("Unknown recipient type for message from %s", npc.displayName))
end

-- And modify processAIResponse to directly use displayMessage
function NPCManagerV3:processAIResponse(npc, participant, response)
    Logger:log("RESPONSE", string.format("Processing AI response for %s: %s",
        npc.displayName,
        HttpService:JSONEncode(response)
    ))

    if response.message then
        Logger:log("CHAT", string.format("Displaying message from %s: %s",
            npc.displayName,
            response.message
        ))
        -- Use displayMessage directly
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
        self:endInteraction(npc, player)
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
    Logger:log("MOVEMENT", string.format("%s starting to follow %s", npc.displayName, player.Name))
    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()

    -- Play walk animation
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        AnimationManager:playAnimation(humanoid, "walk")
    end
    
    Logger:log("STATE", string.format(
        "Follow state set for %s: isFollowing=%s, followTarget=%s",
        npc.displayName,
        tostring(npc.isFollowing),
        player.Name
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
    Logger:log("INTERACTION", string.format("Handling interaction: %s with %s - Message: %s",
        npc.displayName,
        tostring(participant.Name),
        message
    ))

    -- Generate unique interaction ID
    local interactionId = HttpService:GenerateGUID(false)
    
    -- Update interaction state based on participant type
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        -- Player interaction handling
        npc.isInteracting = true
        npc.interactingPlayer = participant
        self:setNPCMovementState(npc, "locked", interactionId)
        
        -- Notify client that conversation started
        NPCChatEvent:FireClient(participant, {
            npcName = npc.displayName,
            type = "started_conversation"
        })
    elseif self:isNPCParticipant(participant) then
        -- NPC-to-NPC interaction handling
        local otherNPC = self.npcs[participant.npcId]
        if otherNPC then
            npc.isInteracting = true
            otherNPC.isInteracting = true
            npc.interactingPlayer = participant
            otherNPC.interactingPlayer = self:createMockParticipant(npc)
            
            self:setNPCMovementState(npc, "locked", interactionId)
            self:setNPCMovementState(otherNPC, "locked", interactionId)
        end
    else
        Logger:warn("Unknown participant type in handleNPCInteraction")
        return
    end

    -- Get and process AI response
    local response = self:getResponseFromAI(npc, participant, message)
    if response then
        self:processAIResponse(npc, participant, response)
    else
        Logger:error(string.format("Failed to get AI response for %s", npc.displayName))
        self:endInteraction(npc, participant)
    end
end

function NPCManagerV3:handlePlayerInteraction(npc, player, message, interactionId)
    -- Lock only the NPC, not the player
    self:setNPCMovementState(npc, "locked", interactionId)
    
    -- Update NPC state
    npc.isInteracting = true
    npc.interactingPlayer = player

    -- Fire client event for chat window
    NPCChatEvent:FireClient(player, {
        npcName = npc.displayName,
        message = message,
        type = "started_conversation"
    })
end

function NPCManagerV3:handleNPCToNPCInteraction(npc1, npc2Participant, message, interactionId)
    local npc2 = self.npcs[npc2Participant.npcId]
    if not npc2 then return end

    -- Lock both NPCs
    self:setNPCMovementState(npc1, "locked", interactionId)
    self:setNPCMovementState(npc2, "locked", interactionId)

    -- Update states
    npc1.isInteracting = true
    npc2.isInteracting = true
    npc1.interactingPlayer = npc2Participant
    npc2.interactingPlayer = self:createMockParticipant(npc1)
end

function NPCManagerV3:setNPCMovementState(npc, state, interactionId)
    if not npc or not npc.model then return end
    
    -- Store previous state if not already stored
    if not self.movementStates[npc.id] then
        self.movementStates[npc.id] = {
            walkSpeed = npc.model.Humanoid.WalkSpeed,
            state = "free",
            interactionId = nil
        }
    end

    local currentState = self.movementStates[npc.id]
    
    if state == "locked" then
        currentState.state = "locked"
        currentState.interactionId = interactionId
        npc.model.Humanoid.WalkSpeed = 0
    elseif state == "free" then
        currentState.state = "free"
        currentState.interactionId = nil
        npc.model.Humanoid.WalkSpeed = currentState.walkSpeed
    end
    
    Logger:log("MOVEMENT", string.format("Set NPC %s movement state to %s", npc.displayName, state))
end

function NPCManagerV3:endInteraction(npc, participant, interactionId)
    if not interactionId then
        Logger:warn("No interactionId provided to endInteraction")
        return
    end

    -- Clean up interaction tracking
    self.activeInteractions[interactionId] = nil

    -- Free the initiating NPC
    self:setNPCMovementState(npc, "free")
    npc.isInteracting = false
    npc.interactingPlayer = nil

    -- If NPC-to-NPC interaction, free the other NPC
    if self:isNPCParticipant(participant) then
        local otherNPC = self.npcs[participant.npcId]
        if otherNPC then
            self:setNPCMovementState(otherNPC, "free")
            otherNPC.isInteracting = false
            otherNPC.interactingPlayer = nil
        end
    end

    -- If player interaction, notify client
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        NPCChatEvent:FireClient(participant, {
            npcName = npc.displayName,
            type = "ended_conversation"
        })
    end

    Logger:log("INTERACTION", string.format("Ended interaction between %s and %s (ID: %s)", 
        npc.displayName, 
        tostring(participant.Name),
        interactionId
    ))
end

function NPCManagerV3:cleanupStaleInteractions()
    local currentTime = tick()
    local staleThreshold = 300 -- 5 minutes

    for interactionId, interaction in pairs(self.activeInteractions) do
        if currentTime - interaction.lastUpdateTime > staleThreshold then
            Logger:warn(string.format("Cleaning up stale interaction: %s", interactionId))
            self:endInteraction(interaction.npc, interaction.participant, interactionId)
        end
    end
end

function NPCManagerV3:updateNPCState(npc)
    if not npc.model or not npc.model.PrimaryPart then return end
    
    self:updateNPCVision(npc)
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then return end

    -- Check if the NPC should be freed from interaction
    if npc.isInteracting then
        if npc.interactingPlayer then
            local shouldEndInteraction = false
            
            if self:isNPCParticipant(npc.interactingPlayer) then
                -- For NPC-to-NPC, check if other NPC is still valid/interacting
                local otherNPC = self.npcs[npc.interactingPlayer.npcId]
                if not otherNPC or not otherNPC.isInteracting then
                    shouldEndInteraction = true
                end
            else
                -- For player interactions, check range
                if not self:isPlayerInRange(npc, npc.interactingPlayer) then
                    shouldEndInteraction = true
                end
            end
            
            if shouldEndInteraction then
                self:endInteraction(npc, npc.interactingPlayer)
            end
        end
    elseif npc.isFollowing then
        self:updateFollowing(npc)
        AnimationManager:playAnimation(humanoid, "walk")
    elseif not npc.isMoving then
        -- Only try to walk if completely free
        if math.random() < 0.05 then  -- 5% chance each update
            self:randomWalk(npc)
        else
            AnimationManager:playAnimation(humanoid, "idle")
        end
    end
end

function NPCManagerV3:isPlayerInRange(npc, player)
    local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local npcPosition = npc.model and npc.model.PrimaryPart

    if playerPosition and npcPosition then
        local distance = (playerPosition.Position - npcPosition.Position).Magnitude
        local inRange = distance <= npc.responseRadius
        Logger:log("VISION", string.format("Distance check for %s to %s: %.2f units (in range: %s)", 
            npc.displayName, 
            player.Name, 
            distance, 
            tostring(inRange)
        ))
        return inRange
    end
    return false
end

function NPCManagerV3:updateFollowing(npc)
    if not npc.isFollowing then
        return -- Exit early if not following
    end
    if not npc.followTarget or not npc.followTarget.Character then
        Logger:log("MOVEMENT", string.format("%s: Follow target lost, stopping follow", npc.displayName))
        self:stopFollowing(npc)
        return
    end

    local targetPosition = npc.followTarget.Character:FindFirstChild("HumanoidRootPart")
    if not targetPosition then
        Logger:log("MOVEMENT", string.format("%s: Cannot find target position, stopping follow", npc.displayName))
        self:stopFollowing(npc)
        return
    end

    local npcPosition = npc.model.PrimaryPart.Position
    local direction = (targetPosition.Position - npcPosition).Unit
    local distance = (targetPosition.Position - npcPosition).Magnitude

    if distance > MIN_FOLLOW_DISTANCE + 1 then
        local newPosition = npcPosition + direction * (distance - MIN_FOLLOW_DISTANCE)
        Logger:log("MOVEMENT", string.format("%s moving to %s", npc.displayName, tostring(newPosition)))
        npc.model.Humanoid:MoveTo(newPosition)
    else
        Logger:log("MOVEMENT", string.format("%s is close enough to target", npc.displayName))
        npc.model.Humanoid:Move(Vector3.new(0, 0, 0)) -- Stop moving
    end

    -- Check if follow duration has expired
    if tick() - npc.followStartTime > FOLLOW_DURATION then
        Logger:log("MOVEMENT", string.format("%s: Follow duration expired, stopping follow", npc.displayName))
        self:stopFollowing(npc)
    end
end

function NPCManagerV3:randomWalk(npc)
    if npc.isInteracting or npc.isMoving then
        Logger:log("MOVEMENT", string.format("%s cannot perform random walk (interacting or moving)", npc.displayName))
        return
    end

    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        local currentPosition = npc.model.PrimaryPart.Position
        local randomOffset = Vector3.new(math.random(-5, 5), 0, math.random(-5, 5))
        local targetPosition = currentPosition + randomOffset

        npc.isMoving = true
        Logger:log("MOVEMENT", string.format("%s starting random walk to %s", 
            npc.displayName, 
            tostring(targetPosition)
        ))

        -- Play walk animation
        AnimationManager:playAnimation(humanoid, "walk")

        humanoid:MoveTo(targetPosition)
        humanoid.MoveToFinished:Connect(function(reached)
            npc.isMoving = false
            if reached then
                Logger:log("MOVEMENT", string.format("%s reached destination", npc.displayName))
            else
                Logger:log("MOVEMENT", string.format("%s failed to reach destination", npc.displayName))
            end

            -- Stop walk animation after reaching
            AnimationManager:stopAnimations(humanoid)
        end)
    else
        Logger:log("ERROR", string.format("%s cannot perform random walk (no Humanoid)", npc.displayName))
    end
end

function NPCManagerV3:getPerceptionData(npc)
	local visibleObjects = {}
	local visiblePlayers = {}
	
	for _, entity in ipairs(npc.visibleEntities) do
		if entity.type == "object" then
			table.insert(visibleObjects, entity.name .. " (" .. entity.objectType .. ")")
		elseif entity.type == "player" then
			table.insert(visiblePlayers, entity.name)
		end
	end

	Logger:log("VISION", string.format("%s perception update: %d objects, %d players", 
		npc.displayName,
		#visibleObjects,
		#visiblePlayers
	))

	return {
		visible_objects = visibleObjects,
		visible_players = visiblePlayers,
		memory = self:getRecentMemories(npc),
	}
end

function NPCManagerV3:getPlayerContext(player)
	local context = {
		player_name = player.Name,
		is_new_conversation = self:isNewConversation(player),
		time_since_last_interaction = self:getTimeSinceLastInteraction(player),
		nearby_players = self:getNearbyPlayerNames(player),
		npc_location = self:getNPCLocation(player),
	}

	Logger:log("STATE", string.format("Context generated for %s: %s", 
		player.Name,
		HttpService:JSONEncode(context)
	))

	return context
end

function NPCManagerV3:getVisibleObjects(npc)
	-- Implementation depends on your game's object system
	return {}
end

function NPCManagerV3:getVisiblePlayers(npc)
	local visiblePlayers = {}
	for _, player in ipairs(Players:GetPlayers()) do
		if self:isPlayerInRange(npc, player) then
			table.insert(visiblePlayers, player.Name)
		end
	end
	return visiblePlayers
end

function NPCManagerV3:getRecentMemories(npc)
	-- Implementation depends on how you store memories
	return {}
end

function NPCManagerV3:isNewConversation(player)
	-- Implementation depends on how you track conversations
	return true
end

function NPCManagerV3:getTimeSinceLastInteraction(player)
	-- Implementation depends on how you track interactions
	return "N/A"
end

function NPCManagerV3:getNearbyPlayerNames(player)
	-- Implementation depends on your game's proximity system
	return {}
end

function NPCManagerV3:getNPCLocation(player)
	-- Implementation depends on how you represent locations in your game
	return "Unknown"
end

function NPCManagerV3:testFollowFunctionality(npcId, playerId)
    local npc = self.npcs[npcId]
    local player = Players:GetPlayerByUserId(playerId)
    
    if npc and player then
        Logger:log("DEBUG", string.format("Testing follow functionality for NPC: %s", npc.displayName))
        self:startFollowing(npc, player)
        wait(5) -- Wait for 5 seconds
        self:updateFollowing(npc)
        wait(5) -- Wait another 5 seconds
        self:stopFollowing(npc)
        Logger:log("DEBUG", string.format("Follow test completed for NPC: %s", npc.displayName))
    else
        Logger:log("ERROR", "Failed to find NPC or player for follow test")
    end
end

function NPCManagerV3:testFollowCommand(npcId, playerId)
	local npc = self.npcs[npcId]
	local player = game.Players:GetPlayerByUserId(playerId)
	if npc and player then
		Logger:log("MOVEMENT", string.format("Testing follow command for %s", npc.displayName))
		self:startFollowing(npc, player)
	else
		Logger:log("ERROR", "Failed to find NPC or player for follow test")
	end
end

function NPCManagerV3:getInteractionClusters(player)
    local clusters = {}
    local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    
    if not playerPosition then
        Logger:log("ERROR", string.format("Cannot get interaction clusters for %s (no character/HumanoidRootPart)", player.Name))
        return clusters
    end

    for _, npc in pairs(self.npcs) do
        local distance = (npc.model.PrimaryPart.Position - playerPosition.Position).Magnitude
        if distance <= npc.responseRadius then
            local addedToCluster = false
            for _, cluster in ipairs(clusters) do
                if (cluster.center - npc.model.PrimaryPart.Position).Magnitude < 10 then
                    table.insert(cluster.npcs, npc)
                    addedToCluster = true
                    Logger:log("INTERACTION", string.format("Added %s to existing cluster", npc.displayName))
                    break
                end
            end
            if not addedToCluster then
                Logger:log("INTERACTION", string.format("Created new cluster for %s", npc.displayName))
                table.insert(clusters, { center = npc.model.PrimaryPart.Position, npcs = { npc } })
            end
        end
    end

    Logger:log("INTERACTION", string.format("Found %d interaction clusters for %s", #clusters, player.Name))
    return clusters
end

-- Update createMockParticipant to include necessary references
function NPCManagerV3:createMockParticipant(npc)
    local MockPlayer = require(game.ServerScriptService.MockPlayer)
    local mockId = tonumber(npc.id) or 0
    local participant = MockPlayer.new(npc.displayName, mockId, "npc")
    
    participant.displayName = npc.displayName
    participant.UserId = mockId
    participant.npcId = npc.id
    participant.model = npc.model
    
    participant.IsA = function(self, className)
        return className == "Player" and false or true
    end
    
    return participant
end

-- Add back initiateNPCInteraction
function NPCManagerV3:initiateNPCInteraction(npc1, npc2)
    if npc1.isInteracting or npc2.isInteracting then
        Logger:log("INTERACTION", "Cannot initiate interaction: one of the NPCs is busy")
        return
    end

    local npc1Participant = self:createMockParticipant(npc1)
    self:handleNPCInteraction(npc2, npc1Participant, "Hello, " .. npc2.displayName .. "!")
end

-- Add new helper functions for NPC state management
function NPCManagerV3:lockNPCInPlace(npc)
    if not npc or not npc.model then return end
    
    npc.isMoving = false
    npc.previousWalkSpeed = npc.model.Humanoid.WalkSpeed -- Store original speed
    npc.model.Humanoid.WalkSpeed = 0
    
    Logger:log("MOVEMENT", string.format("Locked NPC %s in place", npc.displayName))
end

function NPCManagerV3:unlockNPC(npc)
    if not npc or not npc.model then return end
    
    npc.isMoving = true
    if npc.previousWalkSpeed then
        npc.model.Humanoid.WalkSpeed = npc.previousWalkSpeed
    end
    
    Logger:log("MOVEMENT", string.format("Unlocked NPC %s", npc.displayName))
end

-- Add NPC-to-NPC interaction trigger check
function NPCManagerV3:checkNPCInteractions(npc)
    if npc.isInteracting then return end -- Skip if already in interaction

    -- Get current time for cooldown check
    local currentTime = tick()
    if (currentTime - (npc.lastInteractionTime or 0)) < 30 then
        return -- Still in cooldown
    end

    for _, entity in ipairs(npc.visibleEntities) do
        if entity.type == "npc" then
            local otherNPC = entity.instance
            -- Only interact if both NPCs are free and within range
            if not otherNPC.isInteracting 
               and entity.distance < npc.responseRadius 
               and math.random() < 0.02 then -- 2% chance
                
                Logger:log("INTERACTION", string.format("NPC %s initiating conversation with %s",
                    npc.displayName,
                    otherNPC.displayName
                ))
                npc.lastInteractionTime = currentTime
                self:initiateNPCInteraction(npc, otherNPC)
                break
            end
        end
    end
end



function NPCManagerV3:getResponseFromAI(npc, participant, message)
    local interactionState = self.interactionController:getInteractionState(participant)
    local participantMemory = npc.shortTermMemory[participant.UserId] or {}

    -- Ensure we're using the correct participant name
    local participantName = participant.Name
    if self:isNPCParticipant(participant) then
        participantName = participant.displayName or participant.Name
    end

    local data = {
        message = message,
        player_id = tostring(participant.UserId),
        npc_id = npc.id,
        npc_name = npc.displayName,
        participant_name = participantName, -- Add explicit participant name
        system_prompt = npc.system_prompt,
        perception = self:getPerceptionData(npc),
        context = {
            participant_type = self:isNPCParticipant(participant) and "npc" or "player",
            participant_name = participantName,
            is_new_conversation = true,
            interaction_history = npc.chatHistory or {}
        },
        interaction_state = interactionState,
        memory = participantMemory
    }

    local success, response = pcall(function()
        return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
    end)

    if success then
        Logger:log("API", string.format("Raw API response for interaction between %s and %s: %s", 
            npc.displayName,
            participantName,
            response
        ))
        local parsed = HttpService:JSONDecode(response)
        if parsed and parsed.message then
            self.responseCache[self:getCacheKey(npc, participant, message)] = parsed
            npc.shortTermMemory[participant.UserId] = {
                lastInteractionTime = tick(),
                recentTopics = parsed.topics_discussed or {},
                participantName = participantName -- Store the participant name in memory
            }
            return parsed
        else
            Logger:log("ERROR", "Invalid response format received from API")
        end
    else
        Logger:log("ERROR", string.format("Failed to get AI response: %s", tostring(response)))
    end

    return nil
end

-- Add back processAIResponse function
function NPCManagerV3:processAIResponse(npc, participant, response)
    Logger:log("RESPONSE", string.format("Processing AI response for %s: %s",
        npc.displayName,
        HttpService:JSONEncode(response)
    ))

    if response.message then
        Logger:log("CHAT", string.format("Displaying message from %s: %s",
            npc.displayName,
            response.message
        ))
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

return NPCManagerV3

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
            assetId = "7315192066",
            name = "kid",
            description = "This character features a cheerful smile and shaggy brown hair. It sports a green T-shirt with white stars and the number \"8\" printed on it, paired with dark pants. Purple sunglasses add a trendy touch, while white sneakers complete the sporty look, giving the character a fun and casual appearance.",
        },
        {
            assetId = "123821666772514",
            name = "sportymerch",
            description = "This humanoid model features a blocky character dressed in a stylish black tracksuit with yellow accents. The outfit includes an Adidas logo and is complemented by sporty gray shoes. The character sports spiky blonde hair and wears purple sunglasses, adding a cool vibe. A cheerful smile enhances its friendly appearance.",
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
            system_prompt = "I'm sharp", 
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
            system_prompt = "i'm golden", 
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
            system_prompt = "you're clueless but also useful....", 
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
            system_prompt = "You are Oscar, Pets' twin brother. you look for adventures.", 
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
            id = "b11fbfb5-5f46-40cb-9c4c-84ca72b55ac7", 
            displayName = "Pete", 
            name = "Pete", 
            assetId = "7315192066", 
            model = "7315192066", 
            modelName = "Pete", 
            system_prompt = "You like to talk about merch you're selling. Valterpoop aka KrushKen is your boss so you keep an eye out for him or his dad greggytheegg.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(12.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat", 
        }, 
            shortTermMemory = {}, 
        },
    },
}
```

### client/NPCClientHandler.client.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextService = game:GetService("TextService")

-- Get the chat specific RemoteEvent
local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

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

-- Handle incoming NPC chat messages
NPCChatEvent.OnClientEvent:Connect(function(data)
    if data and data.npcName and data.message then
        sendToChat(data.npcName, data.message)
    end
end)

print("NPC Client Chat Handler initialized")
```
