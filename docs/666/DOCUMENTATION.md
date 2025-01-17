# Game 666 Documentation

## Directory Structure

```
games/666/
├── src
│   ├── assets
│   │   ├── npcs
│   │   │   ├── 111993324387868.rbxm
│   │   │   ├── 4613203451.rbxm
│   │   │   ├── 7732869964.rbxm
│   │   │   ├── buff.rbxm
│   │   │   ├── human.rbxm
│   │   │   ├── luna.rbxm
│   │   │   ├── old_wizard.rbxm
│   │   │   ├── pete.rbxm
│   │   │   ├── pete_111993324387868.rbxm
│   │   │   ├── seek.rbxm
│   │   │   └── wizard.rbxm
│   │   └── unknown
│   │       └── buff.rbxm
│   ├── client
│   │   └── NPCClientHandler.client.lua
│   ├── config
│   │   └── GameConfig.lua
│   ├── data
│   │   ├── AssetDatabase.json
│   │   ├── AssetDatabase.lua
│   │   ├── NPCDatabase.json
│   │   └── NPCDatabase.lua
│   ├── debug
│   │   └── NPCSystemDebug.lua
│   ├── server
│   │   ├── AssetInitializer.server.lua
│   │   ├── InteractionController.lua
│   │   ├── Logger.lua
│   │   ├── MainNPCScript.server.lua
│   │   ├── NPCConfigurations.lua
│   │   ├── NPCSystemInitializer.server.lua
│   │   └── PlayerJoinHandler.server.lua
│   ├── services
│   │   └── NPCSpawningService.lua
│   ├── shared
│   │   └── modules
│   │       ├── AssetModule.lua
│   │       └── NPCManagerV3.lua
│   └── init.lua
└── default.project.json
```

## Project Configuration

```json
{
  "name": "EllaAIRobloxGame",
  "tree": {
    "$className": "DataModel",
    "ReplicatedStorage": {
      "$className": "ReplicatedStorage",
      "Shared": {
        "$className": "Folder",
        "NPCManagerV3": {
          "$path": "src/shared/modules/NPCManagerV3.lua"
        },
        "AssetModule": {
          "$path": "src/shared/modules/AssetModule.lua"
        }
      },
      "GameData": {
        "$className": "Folder",
        "AssetDatabase": {
          "$path": "src/data/AssetDatabase.lua"
        },
        "NPCDatabase": {
          "$path": "src/data/NPCDatabase.lua"
        },
        "PlayerDescriptions": {
          "$className": "Folder"
        }
      },
      "NPCChatEvent": {
        "$className": "RemoteEvent"
      }
    },
    "ServerScriptService": {
      "$className": "ServerScriptService",
      "NPCSystemInitializer": {
        "$path": "src/server/NPCSystemInitializer.server.lua"
      },
      "MainNPCScript": {
        "$path": "src/server/MainNPCScript.server.lua"
      },
      "PlayerJoinHandler": {
        "$path": "src/server/PlayerJoinHandler.server.lua"
      },
      "Logger": {
        "$path": "src/server/Logger.lua"
      },
      "InteractionController": {
        "$path": "src/server/InteractionController.lua"
      },
      "AssetInitializer": {
        "$path": "src/server/AssetInitializer.server.lua"
      }
    },
    "StarterPlayer": {
      "$className": "StarterPlayer",
      "StarterPlayerScripts": {
        "$className": "StarterPlayerScripts",
        "NPCClientHandler": {
          "$path": "src/client/NPCClientHandler.client.lua"
        }
      }
    }
  }
}
```

## Source Files

### Client Scripts

#### src/client/NPCClientHandler.client.lua

```lua
-- StarterPlayerScripts/NPCClientHandler.client.lua

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

NPCChatEvent.OnClientEvent:Connect(function(npcName, message)
	if message ~= "The interaction has ended." then
		print("Received NPC message on client: " .. npcName .. " - " .. message)

		-- Display in chat box
		local textChannel = TextChatService.TextChannels.RBXGeneral
		if textChannel then
			textChannel:DisplaySystemMessage(npcName .. ": " .. message)
		else
			warn("RBXGeneral text channel not found.")
		end

		print("NPC Chat Displayed in Chatbox - " .. npcName .. ": " .. message)
	else
		print("Interaction ended with " .. npcName)
	end
end)

print("NPC Client Chat Handler loaded")

```

### Server Scripts

#### src/server/PlayerJoinHandler.server.lua

```lua
--PlayerJoinHandler.server.lua
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Folder to store player descriptions in ReplicatedStorage
local PlayerDescriptionsFolder = ReplicatedStorage:FindFirstChild("PlayerDescriptions")
	or Instance.new("Folder", ReplicatedStorage)
PlayerDescriptionsFolder.Name = "PlayerDescriptions"

local API_URL = "https://roblox.ella-ai-care.com/get_player_description"

-- Function to log data (helpful for testing in Roblox Studio)
local function log(message)
	print("[PlayerJoinHandler] " .. message)
end

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
			log("Received response from API for userId: " .. userId)
			return parsedResponse.description
		else
			log("API response missing 'description' for userId: " .. userId)
			return "No description available"
		end
	else
		log("Failed to get player description from API for userId: " .. userId .. ". Error: " .. tostring(response))
		return "Error retrieving description"
	end
end

-- Function to store player description in ReplicatedStorage
local function storePlayerDescription(playerName, description)
	-- Create or update the player's description in ReplicatedStorage
	local existingDesc = PlayerDescriptionsFolder:FindFirstChild(playerName)
	if existingDesc then
		existingDesc.Value = description
	else
		local playerDesc = Instance.new("StringValue")
		playerDesc.Name = playerName
		playerDesc.Value = description
		playerDesc.Parent = PlayerDescriptionsFolder
	end
end

-- Event handler for when a player joins the game
local function onPlayerAdded(player)
	log("Player joined: " .. player.Name .. " (UserId: " .. player.UserId .. ")")

	-- Get the player's description from the API
	local description = getPlayerDescriptionFromAPI(player.UserId)

	-- Store the description in ReplicatedStorage
	if description then
		storePlayerDescription(player.Name, description)
		log("Stored description for player: " .. player.Name .. " -> " .. description)
	else
		local fallbackDescription = "A player named " .. player.Name
		storePlayerDescription(player.Name, fallbackDescription)
		log("Using fallback description for player: " .. player.Name .. " -> " .. fallbackDescription)
	end
end

-- Connect the PlayerAdded event to the onPlayerAdded function
Players.PlayerAdded:Connect(onPlayerAdded)

-- Ensure logs are displayed at server startup
log("PlayerJoinHandler initialized and waiting for players.")

```

#### src/server/MainNPCScript.server.lua

```lua
-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))

local success, result = pcall(function()
	return require(ServerScriptService:WaitForChild("InteractionController", 5))
end)

if success then
	InteractionController = result
	print("InteractionController loaded successfully")
else
	warn("Failed to load InteractionController:", result)
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
end

-- Call ensureStorage first
ensureStorage()

-- Then initialize NPC system
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))
print("Starting NPC initialization")
local npcManagerV3 = NPCManagerV3.new()
print("NPC Manager created")

for npcId, npcData in pairs(npcManagerV3.npcs) do
	print("NPC spawned: " .. npcData.displayName)
end

local interactionController = npcManagerV3.interactionController

Logger:log("NPC system V3 initialized")

local function checkPlayerProximity()
	for _, player in ipairs(Players:GetPlayers()) do
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if playerPosition then
			for _, npc in pairs(npcManagerV3.npcs) do
				if npc.model and npc.model.PrimaryPart then
					local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
					if distance <= npc.responseRadius and not npc.isInteracting then
						if interactionController:canInteract(player) then
							npcManagerV3:handleNPCInteraction(npc, player, "Hello")
						end
					end
				end
			end
		end
	end
end

local function onPlayerChatted(player, message)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not playerPosition then
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
		npcManagerV3:handleNPCInteraction(closestNPC, player, message)
	end
end

local function setupChatConnections()
	Players.PlayerAdded:Connect(function(player)
		player.Chatted:Connect(function(message)
			onPlayerChatted(player, message)
		end)
	end)
end

setupChatConnections()

local function updateNPCs()
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
		npcManagerV3:endInteraction(interactingNPC, player)
	end
end)

Logger:log("NPC system V3 main script running")

```

#### src/server/NPCSystemInitializer.server.lua

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

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
		print("Found model:", model.Name)
	end
	
	-- Check which required models are missing
	for _, npc in ipairs(npcDatabase.npcs) do
		if not availableModels[npc.model] then
			warn(string.format("Missing required model '%s' for NPC: %s", npc.model, npc.displayName))
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
end

if not ReplicatedStorage:FindFirstChild("EndInteractionEvent") then
	local EndInteractionEvent = Instance.new("RemoteEvent")
	EndInteractionEvent.Name = "EndInteractionEvent"
	EndInteractionEvent.Parent = ReplicatedStorage
end

print("NPC System initialized. Using V3 system.")

```

#### src/server/NPCConfigurations.lua

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

#### src/server/Logger.lua

```lua
local Logger = {}
Logger.logs = {}
Logger.maxBufferSize = 100 -- Set a limit for the buffer

-- Add log entry to buffer
function Logger.log(message)
	table.insert(Logger.logs, message)

	-- Send logs when buffer reaches the max size
	if #Logger.logs >= Logger.maxBufferSize then
		Logger.flushLogs()
	end
end

-- Send logs to heartbeat or external function
function Logger.flushLogs()
	-- Implement the logic to send logs via heartbeat or other methods
	for _, log in ipairs(Logger.logs) do
		print("Sending log:", log) -- Example: replace this with actual sending logic
	end

	-- Clear the buffer after sending
	Logger.logs = {}
end

-- Optional: Schedule regular log flushing
function Logger.startLogFlushing(interval)
	game:GetService("RunService").Heartbeat:Connect(function()
		Logger.flushLogs()
	end)
end

return Logger

```

#### src/server/AssetInitializer.server.lua

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

#### src/server/InteractionController.lua

```lua
-- ServerScriptService/InteractionController.lua

local InteractionController = {}
InteractionController.__index = InteractionController

function InteractionController.new()
    local self = setmetatable({}, InteractionController)
    self.activeInteractions = {}
    return self
end

function InteractionController:startInteraction(player, npc)
    if self.activeInteractions[player] then
        return false
    end
    self.activeInteractions[player] = {npc = npc, startTime = tick()}
    return true
end

function InteractionController:endInteraction(player)
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

### Shared Scripts

#### src/shared/modules/AssetModule.lua

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

#### src/shared/modules/NPCManagerV3.lua

```lua
-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")

local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))

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
	self:loadNPCDatabase()
	return self
end

function NPCManagerV3:loadNPCDatabase()
	local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
	print("Loading NPCs from database:", #npcDatabase.npcs)
	for _, npcData in ipairs(npcDatabase.npcs) do
		self:createNPC(npcData)
	end
end

function NPCManagerV3:createNPC(npcData)
	print("Creating NPC:", npcData.displayName)
	if not workspace:FindFirstChild("NPCs") then
		Instance.new("Folder", workspace).Name = "NPCs"
	end

	local model = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
	if not model then
		warn("Model not found for NPC: " .. npcData.displayName)
		return
	end

	local npcModel = model:Clone()
	npcModel.Parent = workspace.NPCs

	-- Check for necessary parts
	local humanoidRootPart = npcModel:FindFirstChild("HumanoidRootPart")
	local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
	local head = npcModel:FindFirstChild("Head")

	if not humanoidRootPart or not humanoid or not head then
		warn("NPC model " .. npcData.displayName .. " is missing essential parts. Skipping creation.")
		npcModel:Destroy()
		return
	end

	-- Ensure the model has a PrimaryPart
	npcModel.PrimaryPart = humanoidRootPart

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
	print("V3 NPC added: " .. npc.displayName .. ", Total NPCs: " .. self:getNPCCount())
end

function NPCManagerV3:getNPCCount()
	local count = 0
	for _ in pairs(self.npcs) do
		count = count + 1
	end
	return count
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius

	-- Try to parent to HumanoidRootPart, if not available, use any BasePart
	local parent = npc.model:FindFirstChild("HumanoidRootPart") or npc.model:FindFirstChildWhichIsA("BasePart")

	if parent then
		clickDetector.Parent = parent
	else
		warn("Could not find suitable part for ClickDetector on " .. npc.displayName)
		return
	end

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManagerV3:handleNPCInteraction(npc, player, message)
	if self.interactionController:isInGroupInteraction(player) then
		self:handleGroupInteraction(npc, player, message)
		return
	end

	if not self.interactionController:canInteract(player) then
		local interactingNPC = self.interactionController:getInteractingNPC(player)
		if interactingNPC ~= npc then
			return -- Player is interacting with another NPC
		end
	else
		if not self.interactionController:startInteraction(player, npc) then
			return -- Failed to start interaction
		end
	end

	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		return
	end

	npc.isInteracting = true
	npc.interactingPlayer = player

	local response = self:getResponseFromAI(npc, player, message)
	if response then
		npc.lastResponseTime = currentTime
		self:processAIResponse(npc, player, response)
	else
		self:endInteraction(npc, player)
	end
end

function NPCManagerV3:handleGroupInteraction(npc, player, message)
	local group = self.interactionController:getGroupParticipants(player)
	local messages = {}
	for _, participant in ipairs(group) do
		table.insert(messages, { player = participant, message = message })
	end
	local response = self:getGroupResponseFromAI(npc, group, messages)
	self:processGroupAIResponse(npc, group, response)
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

	-- Get the player's avatar description
	local playerDescription = getPlayerDescription(player)

	-- Update the prompt to include the player's description
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

	-- Make the API call
	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
	end)

	if success then
		self:log("Raw API response: " .. response)
		local parsed = HttpService:JSONDecode(response)
		self:log("Parsed API response: " .. HttpService:JSONEncode(parsed))
		if parsed and parsed.message then
			self:log("Parsed API response: " .. HttpService:JSONEncode(parsed))
			self.responseCache[cacheKey] = parsed
			npc.shortTermMemory[player.UserId] = {
				lastInteractionTime = tick(),
				recentTopics = parsed.topics_discussed or {},
			}
			return parsed
		else
			self:log("Invalid response format received from API")
		end
	else
		self:log("Failed to get AI response: " .. tostring(response))
	end

	return nil
end

function NPCManagerV3:log(message)
	print("[NPCManagerV3] " .. os.date("%Y-%m-%d %H:%M:%S") .. ": " .. message)
end

function NPCManagerV3:processAIResponse(npc, player, response)
	print("Processing AI response for " .. npc.displayName .. ":")
	print(HttpService:JSONEncode(response))

	if response.action and response.action.type == "stop_interacting" then
		print("Stopping interaction as per AI response")
		self:endInteraction(npc, player)
		return
	end

	if response.message then
		print("Displaying message: " .. response.message)
		self:displayMessage(npc, response.message, player)
	end

	if response.action then
		print("Executing action: " .. HttpService:JSONEncode(response.action))
		self:executeAction(npc, player, response.action)
	end

	if response.internal_state then
		print("Updating internal state: " .. HttpService:JSONEncode(response.internal_state))
		self:updateInternalState(npc, response.internal_state)
	end
end

function NPCManagerV3:endInteraction(npc, player)
	npc.isInteracting = false
	npc.interactingPlayer = nil
	self.interactionController:endInteraction(player)
	-- Remove this line to prevent the message from appearing in the chat
	-- NPCChatEvent:FireClient(player, npc.displayName, "The interaction has ended.")
	self:log("Interaction ended between " .. npc.displayName .. " and " .. player.Name)
end

function NPCManagerV3:getCacheKey(npc, player, message)
	local context = {
		npcId = npc.id,
		playerId = player.UserId,
		message = message,
		memory = npc.shortTermMemory[player.UserId],
	}
	return HttpService:JSONEncode(context)
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
	print("Updating vision for " .. npc.displayName)
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
				print(npc.displayName .. " sees player: " .. player.Name .. " at distance: " .. distance)
			end
		end
	end

	-- Detect objects and fetch descriptions from AssetDatabase
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
								objectType = assetData.description, -- Use description as the object type
								distance = distance,
								imageUrl = assetData.imageUrl, -- Optionally include the image URL
							})
							print(
								npc.displayName
									.. " sees object: "
									.. assetData.name
									.. " (Description: "
									.. assetData.description
									.. ") at distance: "
									.. distance
							)
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
							print(
								npc.displayName
									.. " sees object: "
									.. object.Name
									.. " (Type: Unknown) at distance: "
									.. distance
							)
						end
					end
				end
			end
		end
	end

	print(npc.displayName .. " vision update complete. Visible entities: " .. #npc.visibleEntities)
end

local ChatService = game:GetService("Chat")

-- In the displayMessage function:
function NPCManagerV3:displayMessage(npc, message, player)
	-- Display chat bubble
	ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)

	-- Fire event to display in chat box
	NPCChatEvent:FireClient(player, npc.displayName, message)
end

function NPCManagerV3:executeAction(npc, player, action)
	self:log("Executing action: " .. action.type .. " for " .. npc.displayName)
	if action.type == "follow" then
		self:log("Starting to follow player: " .. player.Name)
		self:startFollowing(npc, player)
	elseif action.type == "unfollow" or (action.type == "none" and npc.isFollowing) then
		self:log("Stopping following player: " .. player.Name)
		self:stopFollowing(npc)
	elseif action.type == "emote" and action.data and action.data.emote then
		self:log("Playing emote: " .. action.data.emote)
		self:playEmote(npc, action.data.emote)
	elseif action.type == "move" and action.data and action.data.position then
		self:log("Moving to position: " .. tostring(action.data.position))
		self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
	else
		self:log("Unknown action type: " .. action.type)
	end
end

function NPCManagerV3:startFollowing(npc, player)
	self:log(npc.displayName .. " starting to follow " .. player.Name)
	npc.isFollowing = true
	npc.followTarget = player
	npc.followStartTime = tick()
	self:log(
		"Follow state set for "
			.. npc.displayName
			.. ": isFollowing="
			.. tostring(npc.isFollowing)
			.. ", followTarget="
			.. player.Name
	)
end

function NPCManagerV3:updateInternalState(npc, internalState)
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
		else
			warn("Animation not found: " .. emoteName)
		end
	end
end

function NPCManagerV3:moveNPC(npc, targetPosition)
	local Humanoid = npc.model:FindFirstChildOfClass("Humanoid")
	if Humanoid then
		Humanoid:MoveTo(targetPosition)
	end
end

function NPCManagerV3:stopFollowing(npc)
	npc.isFollowing = false
	npc.followTarget = nil
	npc.followStartTime = nil

	-- Actively stop the NPC's movement
	local humanoid = npc.model:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid:MoveTo(npc.model.PrimaryPart.Position)
		humanoid.WalkSpeed = 0 -- Temporarily set walk speed to 0
		wait(0.5) -- Wait a short time
		humanoid.WalkSpeed = 16 -- Reset to default walk speed
	end

	self:log(npc.displayName .. " stopped following and movement halted")
end

function NPCManagerV3:updateNPCState(npc)
	self:updateNPCVision(npc)

	if npc.isFollowing then
		self:updateFollowing(npc)
	elseif npc.isInteracting then
		if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
			self:endInteraction(npc, npc.interactingPlayer)
		end
	elseif not npc.isMoving then
		self:randomWalk(npc)
	end
end

function NPCManagerV3:isPlayerInRange(npc, player)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local npcPosition = npc.model and npc.model.PrimaryPart

	if playerPosition and npcPosition then
		local distance = (playerPosition.Position - npcPosition.Position).Magnitude
		return distance <= npc.responseRadius
	end
	return false
end

function NPCManagerV3:updateFollowing(npc)
	if not npc.isFollowing then
		return -- Exit early if not following
	end
	if not npc.followTarget or not npc.followTarget.Character then
		self:log(npc.displayName .. ": Follow target lost, stopping follow")
		self:stopFollowing(npc)
		return
	end

	local targetPosition = npc.followTarget.Character:FindFirstChild("HumanoidRootPart")
	if not targetPosition then
		self:log(npc.displayName .. ": Cannot find target position, stopping follow")
		self:stopFollowing(npc)
		return
	end

	local npcPosition = npc.model.PrimaryPart.Position
	local direction = (targetPosition.Position - npcPosition).Unit
	local distance = (targetPosition.Position - npcPosition).Magnitude

	if distance > MIN_FOLLOW_DISTANCE + 1 then
		local newPosition = npcPosition + direction * (distance - MIN_FOLLOW_DISTANCE)
		self:log(npc.displayName .. " moving to " .. tostring(newPosition))
		npc.model.Humanoid:MoveTo(newPosition)
	else
		self:log(npc.displayName .. " is close enough to target")
		npc.model.Humanoid:Move(Vector3.new(0, 0, 0)) -- Stop moving
	end

	-- Check if follow duration has expired
	if tick() - npc.followStartTime > FOLLOW_DURATION then
		self:log(npc.displayName .. ": Follow duration expired, stopping follow")
		self:stopFollowing(npc)
	end
end

function NPCManagerV3:randomWalk(npc)
	if npc.isInteracting or npc.isMoving then
		print(npc.displayName .. " cannot perform random walk (interacting or moving)")
		return
	end

	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		local currentPosition = npc.model.PrimaryPart.Position
		local randomOffset = Vector3.new(math.random(-5, 5), 0, math.random(-5, 5))
		local targetPosition = currentPosition + randomOffset

		npc.isMoving = true
		print(npc.displayName .. " starting random walk to " .. tostring(targetPosition))
		humanoid:MoveTo(targetPosition)

		task.spawn(function()
			task.wait(5) -- Wait for 5 seconds or adjust as needed
			npc.isMoving = false
			print(npc.displayName .. " finished random walk")
		end)
	else
		print(npc.displayName .. " cannot perform random walk (no Humanoid)")
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
	return {
		visible_objects = visibleObjects,
		visible_players = visiblePlayers,
		memory = self:getRecentMemories(npc),
	}
end

function NPCManagerV3:getPlayerContext(player)
	return {
		player_name = player.Name,
		is_new_conversation = self:isNewConversation(player),
		time_since_last_interaction = self:getTimeSinceLastInteraction(player),
		nearby_players = self:getNearbyPlayerNames(player),
		npc_location = self:getNPCLocation(player),
	}
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
		self:log("Testing follow functionality for NPC: " .. npc.displayName)
		self:startFollowing(npc, player)
		wait(5) -- Wait for 5 seconds
		self:updateFollowing(npc)
		wait(5) -- Wait another 5 seconds
		self:stopFollowing(npc)
		self:log("Follow test completed for NPC: " .. npc.displayName)
	else
		self:log("Failed to find NPC or player for follow test")
	end
end

function NPCManagerV3:testFollowCommand(npcId, playerId)
	local npc = self.npcs[npcId]
	local player = game.Players:GetPlayerByUserId(playerId)
	if npc and player then
		self:log("Testing follow command for " .. npc.displayName)
		self:startFollowing(npc, player)
	else
		self:log("Failed to find NPC or player for follow test")
	end
end

function NPCManagerV3:getInteractionClusters(player)
	local clusters = {}
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not playerPosition then
		return clusters
	end

	for _, npc in pairs(self.npcs) do
		local distance = (npc.model.PrimaryPart.Position - playerPosition.Position).Magnitude
		if distance <= npc.responseRadius then
			local addedToCluster = false
			for _, cluster in ipairs(clusters) do
				if (cluster.center - npc.model.PrimaryPart.Position).Magnitude < 10 then -- Adjust this threshold as needed
					table.insert(cluster.npcs, npc)
					addedToCluster = true
					break
				end
			end
			if not addedToCluster then
				table.insert(clusters, { center = npc.model.PrimaryPart.Position, npcs = { npc } })
			end
		end
	end
	return clusters
end

return NPCManagerV3

```

### Data Scripts

#### src/data/AssetDatabase.lua

```lua
return {
    {
        assetId = "15571098041",
        name = "Tesla Cybertruck",
        description = "This vehicle features a flat metal, futuristic, angular vehicle reminiscent of a cybertruck. It has a sleek, gray body with distinct sharp edges and minimalistic design. Prominent characteristics include a wide, illuminated front strip, large wheel wells, and a spacious, open cabin. The overall appearance suggests a robust, modern aesthetic.",
    },
    {
        assetId = "13292405039",
        name = "Road Sign Stop",
        description = "An iconic american style street accessory features a classic stop sign, characterized by an octagonal red sign mounted on a simple gray pole. The word STOP is prominently displayed in bold, white capital letters across the center. The design is minimalistic, reflecting typical traffic signage, suitable for various game environments.",
    },
    {
        assetId = "2690222444",
        name = "ReNew Log House",
        description = "This building features a rustic log cabin design, characterized by its brown log walls and a pointed, wooden roof. It has large, circular logs as structural elements, providing a sturdy appearance. The cabin boasts two rectangular windows with a light blue tint, allowing natural light inside, and a simple wooden door at the front entrance.",
    },
    {
        assetId = "11691106540",
        name = "HawaiiClothing Store",
        description = "This building features a stylish, two-story shopping center building with a unique angular design. Its exterior showcases a tan texture with large windows, allowing views into the interior. The roof is flat and painted in a light brown color. Inside, various displays hint at hawaiian themed clothes for sale, creating a storefront vibe with a large sign in front: HawaiiClothing Store",
    },
    {
        assetId = "14215126016",
        name = "Sedan",
        description = "The Roblox asset features a sleek, modern red sports car with a streamlined body design. It has sharp, angular headlights that give it a dynamic look, paired with a black grille. The car's smooth curves are complemented by detailed rims, enhancing its sporty appeal. The interior is visible, showcasing a minimalist dashboard.",
    },
    {
        assetId = "10800319010",
        name = "Seek Killer",
        description = "The asset features a slender, humanoid figure primarily in shiny black, evoking a shadowy appearance. It has an exaggerated, large white eye on its head, contrasting sharply with the dark body. The figure stands still, with a slightly angular aesthetic, giving it a mysterious, eerie vibe typical of horror-themed Roblox assets. This is a potentially dangerous NPC.",
    },
    {
        assetId = "14768974964",
        name = "Wizard",
        description = "The image features a Roblox character dressed as a wizard. He wears a blue robe adorned with moon and star patterns, complemented by a tall, pointed hat that matches the robe's design. His yellow face has a cheerful expression and a long, grey beard. He holds a wand, adding to the magical theme of the attire.",
    },
    {
        assetId = "7315192066",
        name = "Pete",
        description = "This character features a sporty look with a green jersey displaying the number 8 and two white stars. It has dark, textured pants and stylish black-and-white sneakers. Accessories include purple sunglasses, adding a cool vibe. The character has brown hair and a cheerful smile, embodying a casual, playful style.",
    },
    {
        assetId = "1388902922",
        name = "Old Wizard",
        description = "This character features a old character resembling a wizard. He has a long, flowing gray beard and an intense expression. His attire includes a gray and white robe with wide sleeves, accented by a black belt. A tall, pointed hat sits atop his head, completing the magical look. The overall design conveys a classic wizard theme.",
    },
    {
        assetId = "111993324387868",
        name = "Sporty",
        description = "Sporty looking guy with black track suit, sunglasses and visor",
    },
    {
        assetId = "4613203451",
        name = "Police Officer",
        description = "The Roblox asset features a blocky character dressed as a police officer. He wears a bright blue uniform with dark pants and a cap adorned with a badge. The uniform has distinct details like a star badge on the chest. In one hand, he holds a silver handgun, adding to his authoritative appearance.",
    },
    {
        assetId = "7732869964",
        name = "Bacon Head",
        description = "Noob",
    },
}

```

#### src/data/NPCDatabase.lua

```lua
return {
    {
        id = "luna_stargazer",
        displayName = "Luna the Stargazer",
        model = "R6",
        responseRadius = 26,
        assetId = "14768974964",
        spawnPosition = Vector3.new(10, 5, 10),
        system_prompt = [[I am Luna the Stargazer, a mysterious and knowledgeable character who loves to observe the stars.]],
        abilities = {
            "follow",
            "inspect",
        },
        shortTermMemory = {},
    },
    {
        id = "officer_egg",
        displayName = "Officer Egg",
        model = "R6",
        responseRadius = 20,
        assetId = "4613203451",
        spawnPosition = Vector3.new(0, 0, 0),
        system_prompt = [[I am Officer Egg, a diligent law enforcement officer who maintains order.]],
        abilities = {
            "move",
            "chat",
        },
        shortTermMemory = {},
    },
    {
        id = "pete_kid",
        displayName = "Pete the Kid",
        model = "R6",
        responseRadius = 10,
        assetId = "7315192066",
        spawnPosition = Vector3.new(0, 0, 0),
        system_prompt = [[I am Pete the Kid, a playful young character who likes to follow people around.]],
        abilities = {
            "follow",
            "unfollow",
        },
        shortTermMemory = {},
    },
    {
        id = "pete_salesman",
        displayName = "Pete the Salesman",
        model = "R6",
        responseRadius = 20,
        assetId = "111993324387868",
        spawnPosition = Vector3.new(0, 0, 0),
        system_prompt = [[I am Pete the Salesman, a charismatic merchant always ready to chat about my wares.]],
        abilities = {
            "chat",
        },
        shortTermMemory = {},
    },
}

```

### Services

#### src/services/NPCSpawningService.lua

```lua
local NPCSpawningService = {}

local NPCDatabase = require(game:GetService("ReplicatedStorage").Data.NPCDatabase)
local InsertService = game:GetService("InsertService")

-- Remove any NPCs that aren't in our database
function NPCSpawningService:CleanupUnauthorizedNPCs()
    local validIds = {}
    for _, npcData in ipairs(NPCDatabase) do
        validIds[npcData.id] = true
    end

    -- Check workspace for any unauthorized NPCs
    local npcFolder = workspace:FindFirstChild("NPCs")
    if npcFolder then
        for _, model in ipairs(npcFolder:GetChildren()) do
            if not validIds[model.Name] then
                warn("Removing unauthorized NPC:", model.Name)
                model:Destroy()
            end
        end
    end
end

function NPCSpawningService:Initialize()
    print("=== NPC Spawning System Initializing ===")
    
    -- Create NPC folder
    local npcFolder = workspace:FindFirstChild("NPCs") or Instance.new("Folder")
    npcFolder.Name = "NPCs"
    npcFolder.Parent = workspace
    
    -- Clean up unauthorized NPCs
    self:CleanupUnauthorizedNPCs()
    
    -- Spawn authorized NPCs
    local spawnedCount = 0
    for _, npcData in ipairs(NPCDatabase) do
        task.spawn(function()
            local npc = self:SpawnNPC(npcData)
            if npc then
                npc.Parent = npcFolder
                spawnedCount += 1
                print(string.format("Spawned NPC %d/%d: %s", spawnedCount, #NPCDatabase, npcData.displayName))
            end
        end)
        task.wait(0.1) -- Small delay between spawns to prevent throttling
    end
end

function NPCSpawningService:SpawnNPC(npcData)
    -- Validate NPC data
    if not npcData.id or not npcData.assetId then
        warn("Invalid NPC data: Missing ID or AssetID for", npcData.displayName)
        return
    end

    -- Check if NPC already exists
    local existing = workspace:FindFirstChild(npcData.id)
    if existing then
        warn("NPC already exists:", npcData.id)
        return
    end

    -- Convert assetId to number and validate
    local assetId = tonumber(npcData.assetId)
    if not assetId then
        warn("Invalid assetId format for", npcData.displayName, ":", npcData.assetId)
        return
    end

    -- Load character model
    local success, modelOrError = pcall(function()
        return InsertService:LoadAsset(assetId)
    end)

    if not success then
        warn("Failed to load NPC model:", npcData.displayName, "Error:", modelOrError)
        return
    end

    local model = modelOrError:GetChildren()[1]
    if not model then
        warn("No model found in loaded asset for:", npcData.displayName)
        modelOrError:Destroy()
        return
    end

    -- Set up the NPC
    model.Name = npcData.id
    
    -- Ensure proper spawn position
    local spawnCFrame = CFrame.new(npcData.spawnPosition)
    if npcData.spawnPosition == Vector3.new(0, 0, 0) then
        -- Fallback spawn position if none specified
        spawnCFrame = CFrame.new(0, 5, 0)
        warn("Using fallback spawn position for:", npcData.displayName)
    end
    
    model:PivotTo(spawnCFrame)
    model.Parent = workspace

    -- Clean up the asset container
    modelOrError:Destroy()

    -- Add Humanoid if not present
    if not model:FindFirstChild("Humanoid") then
        local humanoid = Instance.new("Humanoid")
        humanoid.Parent = model
    end

    return model
end

return NPCSpawningService 
```

### Configuration

#### src/config/GameConfig.lua

```lua
return {
    NPCSystem = {
        version = "new", -- "new" or "v3"
        debug = true,
        spawnDelay = 0.5, -- delay between spawning each NPC
    }
} 
```

### Debug Scripts

#### src/debug/NPCSystemDebug.lua

```lua
local function findAllNPCScripts()
    local function searchInContainer(container, results)
        for _, item in ipairs(container:GetDescendants()) do
            if item:IsA("Script") and 
               (item.Name:find("NPC") or item.Name:find("npc")) then
                table.insert(results, item:GetFullName())
            end
        end
    end
    
    local results = {}
    searchInContainer(game:GetService("ServerScriptService"), results)
    searchInContainer(game:GetService("ReplicatedStorage"), results)
    
    print("=== Found NPC-related scripts ===")
    for _, path in ipairs(results) do
        print(path)
    end
    print("===============================")
end

return {
    findAllNPCScripts = findAllNPCScripts
} 
```
