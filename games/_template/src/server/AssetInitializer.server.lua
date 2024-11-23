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
