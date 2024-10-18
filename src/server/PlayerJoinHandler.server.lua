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
