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
│   ├── MainNPCScript.server.lua
│   ├── NPCConfigurations.lua
│   ├── NPCSystemInitializer.server.lua
│   └── PlayerJoinHandler.server.lua
└── shared
    ├── AnimationManager.lua
    ├── AssetModule.lua
    └── NPCManagerV3.lua
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

```

### server/ChatSetup.server.lua

```lua
local ChatService = game:GetService("Chat")
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

Logger:log("SYSTEM", "Setting up chat service")

-- Example: Enabling chat (if needed)
if ChatService then
    local success, result = pcall(function()
        ChatService:ChatVersion("TextChatService")
    end)
    
    if success then
        Logger:log("SYSTEM", "Chat service initialized successfully")
    else
        Logger:log("ERROR", string.format("Unable to initialize chat service: %s", tostring(result)))
    end
else
    Logger:log("ERROR", "Unable to get Chat service: service not available")
end

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
local function storeAssetDescriptions(assetId, name, description, imageUrl)
	local assetEntry = LocalDB:FindFirstChild(assetId)
	if assetEntry then
		assetEntry:Destroy() -- Remove existing entry to ensure we're updating all fields
	end

	assetEntry = Instance.new("Folder")
	assetEntry.Name = assetId
	assetEntry.Parent = LocalDB

	local nameValue = Instance.new("StringValue")
	nameValue.Name = "Name"
	nameValue.Value = name
	nameValue.Parent = assetEntry

	local descValue = Instance.new("StringValue")
	descValue.Name = "Description"
	descValue.Value = description
	descValue.Parent = assetEntry

	local imageValue = Instance.new("StringValue")
	imageValue.Name = "ImageUrl"
	imageValue.Value = imageUrl
	imageValue.Parent = assetEntry

	-- Add to lookup table
	AssetLookup[name] = assetId

	print(
		string.format(
			"Stored asset: ID: %s, Name: %s, Description: %s",
			assetId,
			name,
			string.sub(description, 1, 50) .. "..."
		)
	)
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

function NPCManagerV3.new()
    local self = setmetatable({}, NPCManagerV3)
    self.npcs = {}
    self.responseCache = {}
    self.interactionController = InteractionController.new()
    Logger:log("SYSTEM", "Initializing NPCManagerV3")
    self:loadNPCDatabase()
    return self
end

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
    }

    -- Position the NPC
    humanoidRootPart.CFrame = CFrame.new(npcData.spawnPosition)

    self:setupClickDetector(npc)
    self.npcs[npc.id] = npc
    Logger:log("NPC", string.format("NPC added: %s (Total NPCs: %d)", npc.displayName, self:getNPCCount()))
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

function NPCManagerV3:handleNPCInteraction(npc, player, message)
    Logger:log("INTERACTION", string.format("Handling interaction: %s with %s - Message: %s",
        npc.displayName,
        player.Name,
        message
    ))

    if self.interactionController:isInGroupInteraction(player) then
        Logger:log("INTERACTION", string.format("Group interaction detected for %s", player.Name))
        self:handleGroupInteraction(npc, player, message)
        return
    end

    if not self.interactionController:canInteract(player) then
        local interactingNPC = self.interactionController:getInteractingNPC(player)
        if interactingNPC ~= npc then
            Logger:log("INTERACTION", string.format("Player %s is already interacting with another NPC", player.Name))
            return
        end
    else
        if not self.interactionController:startInteraction(player, npc) then
            Logger:log("ERROR", string.format("Failed to start interaction between %s and %s", npc.displayName, player.Name))
            return
        end
    end

    local currentTime = tick()
    if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
        Logger:log("INTERACTION", string.format("Interaction cooldown for %s (%.1f seconds remaining)", 
            npc.displayName, 
            RESPONSE_COOLDOWN - (currentTime - npc.lastResponseTime)
        ))
        return
    end

    npc.isInteracting = true
    npc.interactingPlayer = player

    local response = self:getResponseFromAI(npc, player, message)
    if response then
        npc.lastResponseTime = currentTime
        self:processAIResponse(npc, player, response)
    else
        Logger:log("ERROR", string.format("Failed to get AI response for %s", npc.displayName))
        self:endInteraction(npc, player)
    end
end

function NPCManagerV3:handleGroupInteraction(npc, player, message)
    local group = self.interactionController:getGroupParticipants(player)
    Logger:log("INTERACTION", string.format("Processing group interaction for %s with %d participants", 
        npc.displayName, 
        #group
    ))

    local messages = {}
    for _, participant in ipairs(group) do
        table.insert(messages, { player = participant, message = message })
    end

    local response = self:getGroupResponseFromAI(npc, group, messages)
    if response then
        self:processGroupAIResponse(npc, group, response)
    else
        Logger:log("ERROR", string.format("Failed to get group AI response for %s", npc.displayName))
    end
end

-- Function to get the player's description
local function getPlayerDescription(player)
	local playerDescFolder = ReplicatedStorage:FindFirstChild("PlayerDescriptions")
	if playerDescFolder then
		local description = playerDescFolder:FindFirstChild(player.Name)
		if description then
			return description.Value
		end
	end
	return "No description available."
end

-- Modified getResponseFromAI to include player description
function NPCManagerV3:getResponseFromAI(npc, player, message)
    local interactionState = self.interactionController:getInteractionState(player)
    local playerMemory = npc.shortTermMemory[player.UserId] or {}

    local cacheKey = self:getCacheKey(npc, player, message)
    if self.responseCache[cacheKey] then
        return self.responseCache[cacheKey]
    end

    local playerDescription = getPlayerDescription(player)

    local data = {
        message = message,
        player_id = tostring(player.UserId),
        npc_id = npc.id,
        npc_name = npc.displayName,
        system_prompt = npc.system_prompt .. "\n\nPlayer Description: " .. playerDescription,
        perception = self:getPerceptionData(npc),
        context = self:getPlayerContext(player),
        interaction_state = interactionState,
        memory = playerMemory,
        limit = 200,
    }

    local success, response = pcall(function()
        return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
    end)

    if success then
        Logger:log("API", string.format("Raw API response: %s", response))
        local parsed = HttpService:JSONDecode(response)
        Logger:log("API", string.format("Parsed API response: %s", HttpService:JSONEncode(parsed)))
        if parsed and parsed.message then
            self.responseCache[cacheKey] = parsed
            npc.shortTermMemory[player.UserId] = {
                lastInteractionTime = tick(),
                recentTopics = parsed.topics_discussed or {},
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

function NPCManagerV3:processAIResponse(npc, player, response)
    Logger:log("RESPONSE", string.format("Processing AI response for %s: %s",
        npc.displayName,
        HttpService:JSONEncode(response)
    ))

    if response.action and response.action.type == "stop_interacting" then
        Logger:log("ACTION", string.format("Stopping interaction for %s as per AI response", npc.displayName))
        self:endInteraction(npc, player)
        return
    end

    if response.message then
        Logger:log("CHAT", string.format("Displaying message from %s: %s",
            npc.displayName,
            response.message
        ))
        self:displayMessage(npc, response.message, player)
    end

    if response.action then
        Logger:log("ACTION", string.format("Executing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.action)
        ))
        self:executeAction(npc, player, response.action)
    end

    if response.internal_state then
        Logger:log("STATE", string.format("Updating internal state for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.internal_state)
        ))
        self:updateInternalState(npc, response.internal_state)
    end
end

function NPCManagerV3:endInteraction(npc, player)
	npc.isInteracting = false
	npc.interactingPlayer = nil
	self.interactionController:endInteraction(player)
	Logger:log("INTERACTION", string.format("Interaction ended between %s and %s", 
		npc.displayName, 
		player.Name
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
    Logger:log("VISION", string.format("Updating vision for %s", npc.displayName))
    npc.visibleEntities = {}
    local npcPosition = npc.model.PrimaryPart.Position

    -- Detect players
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "player",
                    name = player.Name,
                    distance = distance,
                })
                Logger:log("VISION", string.format("%s sees player: %s at distance: %.2f",
                    npc.displayName,
                    player.Name,
                    distance
                ))
            end
        end
    end

    -- Detect objects and fetch descriptions from AssetDatabase
    local detectedObjects = {}
    for _, object in ipairs(workspace:GetChildren()) do
        if object:IsA("Model") and object ~= npc.model then
            local primaryPart = object.PrimaryPart or object:FindFirstChildWhichIsA("BasePart")
            if primaryPart then
                local distance = (primaryPart.Position - npcPosition).Magnitude
                if distance <= VISION_RANGE then
                    -- Fetch asset data from the AssetDatabase
                    local assetData = getAssetData(object.Name)
                    if assetData then
                        local key = object.Name .. "_" .. assetData.assetId
                        if not detectedObjects[key] then
                            detectedObjects[key] = true
                            table.insert(npc.visibleEntities, {
                                type = "object",
                                name = assetData.name,
                                objectType = assetData.description,
                                distance = distance,
                                imageUrl = assetData.imageUrl,
                            })
                            Logger:log("VISION", string.format("%s sees object: %s (Description: %s) at distance: %.2f",
                                npc.displayName,
                                assetData.name,
                                assetData.description,
                                distance
                            ))
                        end
                    else
                        -- If asset data is not found, fall back to default behavior
                        local key = object.Name .. "_Unknown"
                        if not detectedObjects[key] then
                            detectedObjects[key] = true
                            table.insert(npc.visibleEntities, {
                                type = "object",
                                name = object.Name,
                                objectType = "Unknown",
                                distance = distance,
                            })
                            Logger:log("VISION", string.format("%s sees object: %s (Type: Unknown) at distance: %.2f",
                                npc.displayName,
                                object.Name,
                                distance
                            ))
                        end
                    end
                end
            end
        end
    end

    Logger:log("VISION", string.format("%s vision update complete. Visible entities: %d",
        npc.displayName,
        #npc.visibleEntities
    ))
end

function NPCManagerV3:displayMessage(npc, message, player)
    Logger:log("CHAT", string.format("NPC %s sending message to %s: %s", 
        npc.displayName,
        player and player.Name or "all players",
        message
    ))

    -- Display chat bubble
    ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)

    -- Fire event to display in chat box
    if player then
        NPCChatEvent:FireClient(player, npc.displayName, message)
    else
        NPCChatEvent:FireAllClients(npc.displayName, message)
    end
end

function NPCManagerV3:executeAction(npc, player, action)
    Logger:log("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    if action.type == "follow" then
        Logger:log("MOVEMENT", string.format("Starting to follow player: %s", player.Name))
        self:startFollowing(npc, player)
    elseif action.type == "unfollow" or (action.type == "none" and npc.isFollowing) then
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

function NPCManagerV3:updateNPCState(npc)
    self:updateNPCVision(npc)

    local humanoid = npc.model:FindFirstChild("Humanoid")

    if npc.isFollowing then
        self:updateFollowing(npc)
        if humanoid then
            AnimationManager:playAnimation(humanoid, "walk")
        end
    elseif npc.isInteracting then
        if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
            Logger:log("INTERACTION", string.format("%s moved out of range, ending interaction", npc.interactingPlayer.Name))
            self:endInteraction(npc, npc.interactingPlayer)
        end
    elseif not npc.isMoving then
        -- Trigger idle animation if the NPC is not moving or following
        if humanoid then
            AnimationManager:playAnimation(humanoid, "idle")
        end
        self:randomWalk(npc)
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

return NPCManagerV3

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
-- StarterPlayerScripts/NPCClientHandler.client.lua

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

-- Initialize Logger
local Logger
local function initializeLogger()
    local success, result = pcall(function()
        return require(ReplicatedStorage:WaitForChild("Logger", 10))
    end)

    if success then
        Logger = result
    else
        -- Fallback logger
        Logger = {
            log = function(_, category, message)
                print(string.format("[%s] %s", category, message))
            end
        }
    end
end

initializeLogger()

local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

NPCChatEvent.OnClientEvent:Connect(function(npcName, message)
    if message ~= "The interaction has ended." then
        Logger:log("CHAT", string.format("Received NPC message: %s - %s", npcName, message))

        -- Display in chat box
        local textChannel = TextChatService.TextChannels.RBXGeneral
        if textChannel then
            textChannel:DisplaySystemMessage(npcName .. ": " .. message)
            Logger:log("CHAT", string.format("Message displayed in chat: %s: %s", npcName, message))
        else
            Logger:log("ERROR", "RBXGeneral text channel not found")
        end

        Logger:log("CHAT", string.format("NPC Chat processed - %s: %s", npcName, message))
    else
        Logger:log("CHAT", string.format("Interaction ended with %s", npcName))
    end
end)

Logger:log("SYSTEM", "NPC Client Chat Handler loaded")

```
