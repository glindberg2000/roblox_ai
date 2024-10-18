local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PlayerDescriptions = {}

-- API endpoint (dummy API)
local API_URL = "https://roblox.ella-ai-care.com/get_player_description"

-- Function to log data (helpful for testing in Roblox Studio)
local function log(message)
	print("[PlayerJoinHandler] " .. message)
end

-- Function to send player ID to an external API and get description
local function getPlayerDescriptionFromAPI(userId)
	local data = {
		user_id = tostring(userId),
	}

	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson)
	end)

	if success then
		local parsedResponse = HttpService:JSONDecode(response)

		-- Add a check for nil values
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

-- Event handler for when a player joins
local function onPlayerAdded(player)
	log("Player joined: " .. player.Name .. " (UserId: " .. player.UserId .. ")")

	-- Get the player's description from the API (or use a fallback description)
	local description = getPlayerDescriptionFromAPI(player.UserId)

	-- Store the description (fallback if API call fails)
	if description then
		PlayerDescriptions[player.UserId] = description
		log("Stored description for player: " .. player.Name .. " -> " .. description)
	else
		local fallbackDescription = "A player named " .. player.Name
		PlayerDescriptions[player.UserId] = fallbackDescription
		log("Using fallback description for player: " .. player.Name .. " -> " .. fallbackDescription)
	end
end

-- Connect the PlayerAdded event to the onPlayerAdded function
Players.PlayerAdded:Connect(onPlayerAdded)

-- Ensure logs are displayed at server startup
log("PlayerJoinHandler initialized and waiting for players.")
