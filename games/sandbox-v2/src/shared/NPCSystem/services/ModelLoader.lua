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

function ModelLoader.sanitizeModel(model)
    -- Remove unwanted scripts
    for _, item in ipairs(model:GetDescendants()) do
        if item:IsA("Script") or item:IsA("LocalScript") then
            if item.Name:match("hunt") or item.Name:match("feed") or item.Name:match("unstuck") then
                LoggerService:info("MODEL", string.format("Removing script: %s from model", item.Name))
                item:Destroy()
            end
        end
    end
    return model
end

function ModelLoader.loadModel(modelId, modelType)
    LoggerService:info("MODEL", string.format("ModelLoader v%s - Loading model: %s", ModelLoader.Version, modelId))
    
    -- Try local file first
    local model = nil
    local assetsFolders = ServerStorage:FindFirstChild("Assets")
    if assetsFolders then
        local npcsFolder = assetsFolders:FindFirstChild("npcs")
        if npcsFolder then
            model = npcsFolder:FindFirstChild(modelId)
        end
    end
    
    -- If local file not found, try Toolbox loading
    if not model then
        LoggerService:info("MODEL", string.format("Local model not found, trying Toolbox for ID: %s", modelId))
        
        -- Try multiple Toolbox loading methods with proper permissions
        local success, result = pcall(function()
            -- Try with game creator ID first
            local insertService = game:GetService("InsertService")
            insertService.AllowInsertFreeModels = true
            
            -- Try direct asset loading
            local asset = insertService:LoadAsset(tonumber(modelId))
            if asset then
                -- Save to ServerStorage for future use
                local model = asset:GetChildren()[1]
                if model then
                    local npcsFolder = ServerStorage:FindFirstChild("Assets") 
                        and ServerStorage.Assets:FindFirstChild("npcs")
                    
                    if npcsFolder then
                        local savedModel = model:Clone()
                        savedModel.Name = modelId
                        savedModel.Parent = npcsFolder
                        LoggerService:info("MODEL", string.format("Saved model %s to ServerStorage for future use", modelId))
                    end
                    
                    return model
                end
            end
            
            -- Try marketplace if direct loading fails
            return insertService:LoadAssetVersion(tonumber(modelId))
        end)
        
        if success and result then
            model = result
            LoggerService:info("MODEL", string.format("Successfully loaded model from Toolbox: %s", modelId))
        else
            LoggerService:error("MODEL", string.format("Failed to load model from Toolbox: %s. Error: %s", modelId, tostring(result)))
            LoggerService:warn("MODEL", string.format("Please pre-load model %s in Studio and save to ServerStorage/Assets/npcs", modelId))
        end
    end
    
    if model and model:IsA("Model") then
        model = ModelLoader.sanitizeModel(model:Clone())
        LoggerService:info("MODEL", string.format("Found model: Type=%s, Name=%s, Children=%d", 
            model.ClassName, model.Name, #model:GetChildren()))
        return model
    end
    
    LoggerService:error("MODEL", string.format("Model %s not found locally or in Toolbox", modelId))
    return nil
end

return ModelLoader 