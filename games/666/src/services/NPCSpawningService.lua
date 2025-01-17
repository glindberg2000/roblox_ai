local NPCSpawningService = {}

local NPCDatabase = require(game:GetService("ReplicatedStorage").Data.NPCDatabase)
local InsertService = game:GetService("InsertService")

-- Remove any NPCs that aren't in our database
function NPCSpawningService:CleanupUnauthorizedNPCs()
    local validIds = {}
    for _, npcData in ipairs(NPCDatabase) do
        validIds[npcData.id] = true
    end

    -- Check workspace for any unauthorized NPCs
    local npcFolder = workspace:FindFirstChild("NPCs")
    if npcFolder then
        for _, model in ipairs(npcFolder:GetChildren()) do
            if not validIds[model.Name] then
                warn("Removing unauthorized NPC:", model.Name)
                model:Destroy()
            end
        end
    end
end

function NPCSpawningService:Initialize()
    print("=== NPC Spawning System Initializing ===")
    
    -- Create NPC folder
    local npcFolder = workspace:FindFirstChild("NPCs") or Instance.new("Folder")
    npcFolder.Name = "NPCs"
    npcFolder.Parent = workspace
    
    -- Clean up unauthorized NPCs
    self:CleanupUnauthorizedNPCs()
    
    -- Spawn authorized NPCs
    local spawnedCount = 0
    for _, npcData in ipairs(NPCDatabase) do
        task.spawn(function()
            local npc = self:SpawnNPC(npcData)
            if npc then
                npc.Parent = npcFolder
                spawnedCount += 1
                print(string.format("Spawned NPC %d/%d: %s", spawnedCount, #NPCDatabase, npcData.displayName))
            end
        end)
        task.wait(0.1) -- Small delay between spawns to prevent throttling
    end
end

function NPCSpawningService:SpawnNPC(npcData)
    -- Validate NPC data
    if not npcData.id or not npcData.assetId then
        warn("Invalid NPC data: Missing ID or AssetID for", npcData.displayName)
        return
    end

    -- Check if NPC already exists
    local existing = workspace:FindFirstChild(npcData.id)
    if existing then
        warn("NPC already exists:", npcData.id)
        return
    end

    -- Convert assetId to number and validate
    local assetId = tonumber(npcData.assetId)
    if not assetId then
        warn("Invalid assetId format for", npcData.displayName, ":", npcData.assetId)
        return
    end

    -- Load character model
    local success, modelOrError = pcall(function()
        return InsertService:LoadAsset(assetId)
    end)

    if not success then
        warn("Failed to load NPC model:", npcData.displayName, "Error:", modelOrError)
        return
    end

    local model = modelOrError:GetChildren()[1]
    if not model then
        warn("No model found in loaded asset for:", npcData.displayName)
        modelOrError:Destroy()
        return
    end

    -- Set up the NPC
    model.Name = npcData.id
    
    -- Ensure proper spawn position
    local spawnCFrame = CFrame.new(npcData.spawnPosition)
    if npcData.spawnPosition == Vector3.new(0, 0, 0) then
        -- Fallback spawn position if none specified
        spawnCFrame = CFrame.new(0, 5, 0)
        warn("Using fallback spawn position for:", npcData.displayName)
    end
    
    model:PivotTo(spawnCFrame)
    model.Parent = workspace

    -- Clean up the asset container
    modelOrError:Destroy()

    -- Add Humanoid if not present
    if not model:FindFirstChild("Humanoid") then
        local humanoid = Instance.new("Humanoid")
        humanoid.Parent = model
    end

    return model
end

return NPCSpawningService 