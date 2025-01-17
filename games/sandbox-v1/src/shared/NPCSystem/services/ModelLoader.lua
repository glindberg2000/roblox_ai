local ModelLoader = {}
ModelLoader.Version = "1.0.1"

local ServerStorage = game:GetService("ServerStorage")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

function ModelLoader.init()
    LoggerService:info("SYSTEM", string.format("ModelLoader v%s initialized", ModelLoader.Version))
    
    -- Check initial folder structure
    if ServerStorage:FindFirstChild("Assets") then
        LoggerService:info("MODEL", "Found Assets folder in ServerStorage")
        if ServerStorage.Assets:FindFirstChild("npcs") then
            LoggerService:info("MODEL", "Found npcs folder in Assets")
            local models = ServerStorage.Assets.npcs:GetChildren()
            LoggerService:info("MODEL", string.format("Found %d models in npcs folder:", #models))
            for _, model in ipairs(models) do
                LoggerService:info("MODEL", " - " .. model.Name)
            end
        else
            LoggerService:error("MODEL", "npcs folder not found in Assets")
        end
    else
        LoggerService:error("MODEL", "Assets folder not found in ServerStorage")
    end
end

function ModelLoader.loadModel(modelId, modelType)
    LoggerService:info("MODEL", string.format("ModelLoader v%s - Loading model: %s", ModelLoader.Version, modelId))
    
    -- Find all Assets folders
    local assetsFolders = {}
    for _, child in ipairs(ServerStorage:GetChildren()) do
        if child.Name == "Assets" then
            table.insert(assetsFolders, child)
        end
    end
    
    LoggerService:info("MODEL", string.format("Found %d Assets folders", #assetsFolders))
    
    -- Use only the first Assets folder and warn about duplicates
    if #assetsFolders > 1 then
        LoggerService:warn("MODEL", "Multiple Assets folders found - using only the first one")
        -- Remove extra Assets folders
        for i = 2, #assetsFolders do
            LoggerService:warn("MODEL", string.format("Removing duplicate Assets folder %d", i))
            assetsFolders[i]:Destroy()
        end
    end
    
    local assetsFolder = assetsFolders[1]
    if not assetsFolder then
        LoggerService:error("MODEL", "No Assets folder found")
        return nil
    end
    
    local npcsFolder = assetsFolder:FindFirstChild("npcs")
    if not npcsFolder then
        LoggerService:error("MODEL", "No npcs folder found in Assets")
        return nil
    end
    
    local model = npcsFolder:FindFirstChild(modelId)
    if not model then
        -- Try loading from RBXM file
        local success, result = pcall(function()
            return game:GetService("InsertService"):LoadLocalAsset(string.format("%s/src/assets/npcs/%s.rbxm", game:GetService("ServerScriptService").Parent.Parent.Name, modelId))
        end)
        if success and result then
            model = result
        end
    end
    
    if model and model:IsA("Model") then
        LoggerService:info("MODEL", string.format("Found model: Type=%s, Name=%s, Children=%d", 
            model.ClassName, model.Name, #model:GetChildren()))
        
        -- Log all model parts
        for _, child in ipairs(model:GetChildren()) do
            LoggerService:debug("MODEL", string.format("  - %s (%s)", child.Name, child.ClassName))
        end
        
        return model:Clone()
    end
    
    LoggerService:error("MODEL", string.format("Model %s not found", modelId))
    return nil
end

return ModelLoader 