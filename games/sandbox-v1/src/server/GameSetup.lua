local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function cleanupDuplicateFolders()
    -- Clean up duplicate Assets folders
    local assetsFolders = {}
    for _, child in ipairs(ServerStorage:GetChildren()) do
        if child.Name == "Assets" then
            table.insert(assetsFolders, child)
        end
    end
    
    if #assetsFolders > 1 then
        warn("Found multiple Assets folders - cleaning up...")
        -- Keep the first one, remove others
        for i = 2, #assetsFolders do
            assetsFolders[i]:Destroy()
        end
    end
end

local function ensureRequiredFolders()
    -- Ensure Assets folder exists
    local assets = ServerStorage:FindFirstChild("Assets")
    if not assets then
        assets = Instance.new("Folder")
        assets.Name = "Assets"
        assets.Parent = ServerStorage
    end
    
    -- Ensure npcs folder exists
    local npcs = assets:FindFirstChild("npcs")
    if not npcs then
        npcs = Instance.new("Folder")
        npcs.Name = "npcs"
        npcs.Parent = assets
    end
    
    -- Ensure Shared folder exists in ReplicatedStorage
    local shared = ReplicatedStorage:FindFirstChild("Shared")
    if not shared then
        shared = Instance.new("Folder")
        shared.Name = "Shared"
        shared.Parent = ReplicatedStorage
    end
end

local function init()
    cleanupDuplicateFolders()
    ensureRequiredFolders()
end

init() 