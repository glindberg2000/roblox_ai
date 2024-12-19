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
