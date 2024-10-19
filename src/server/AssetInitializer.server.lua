-- AssetInitializer.server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Load the AssetDatabase file directly
local AssetDatabase = require(game:GetService("ServerScriptService").AssetDatabase)

-- Create or get LocalDB in ReplicatedStorage for storing asset descriptions
local LocalDB = ReplicatedStorage:FindFirstChild("LocalDB") or Instance.new("Folder", ReplicatedStorage)
LocalDB.Name = "LocalDB"

-- Function to store asset descriptions in ReplicatedStorage
local function storeAssetDescriptions(assetId, name, description, imageUrl)
	local assetEntry = LocalDB:FindFirstChild(assetId)
	if not assetEntry then
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
	end
end

-- Initialize all assets from the local AssetDatabase
local function initializeAssets()
	for assetId, assetData in pairs(AssetDatabase.assets) do
		storeAssetDescriptions(assetId, assetData.name, assetData.description, assetData.imageUrl)
		print("Loaded asset description for AssetId: " .. assetId)
	end
end

initializeAssets()
print("All assets initialized from local database.")
