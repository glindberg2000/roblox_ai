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
