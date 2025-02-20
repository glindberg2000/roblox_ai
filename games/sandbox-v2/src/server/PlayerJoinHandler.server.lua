--PlayerJoinHandler.server.lua
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local LettaConfig = require(NPCSystem.config.LettaConfig)

-- Initialize Logger
local Logger = require(NPCSystem.services.LoggerService)

-- Folder to store player descriptions in ReplicatedStorage
local PlayerDescriptionsFolder = ReplicatedStorage:FindFirstChild("PlayerDescriptions")
	or Instance.new("Folder", ReplicatedStorage)
PlayerDescriptionsFolder.Name = "PlayerDescriptions"

-- Update API_URL construction
local API_URL = LettaConfig.BASE_URL .. LettaConfig.ENDPOINTS.PLAYER_DESCRIPTION

-- Function to send player ID to an external API and get a description
local function getPlayerDescriptionFromAPI(userId)
	local data = { user_id = tostring(userId) }
	
	Logger:debug("API", string.format(
		"Requesting player description - URL: %s, Data: %s",
		API_URL,
		HttpService:JSONEncode(data)
	))

	local success, response = pcall(function()
		return HttpService:PostAsync(
			API_URL, 
			HttpService:JSONEncode(data),
			Enum.HttpContentType.ApplicationJson,
			false
		)
	end)

	if success then
		local parsedResponse = HttpService:JSONDecode(response)
		Logger:debug("API", string.format(
			"Raw API Response: %s",
			response
		))

		if parsedResponse and parsedResponse.description then
			Logger:info("API", string.format("Received description for userId: %s", userId))
			return parsedResponse.description
		else
			Logger:error("API", string.format(
				"API response missing 'description' field for userId: %s. Full response: %s",
				userId,
				response
			))
			return "No description available"
		end
	else
		Logger:error("API", string.format(
			"API call failed for userId: %s. URL: %s, Error: %s",
			userId,
			API_URL,
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
