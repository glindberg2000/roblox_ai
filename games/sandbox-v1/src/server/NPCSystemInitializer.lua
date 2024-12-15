local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

-- Ensure required folders exist
local function ensureRequiredServices()
    -- Create Shared folder if it doesn't exist
    local shared = ReplicatedStorage:FindFirstChild("Shared") or Instance.new("Folder")
    shared.Name = "Shared"
    shared.Parent = ReplicatedStorage
    
    -- Create NPCSystem folder if it doesn't exist
    local npcSystem = shared:FindFirstChild("NPCSystem") or Instance.new("Folder")
    npcSystem.Name = "NPCSystem"
    npcSystem.Parent = shared
    
    -- Create services folder if it doesn't exist
    local services = npcSystem:FindFirstChild("services") or Instance.new("Folder")
    services.Name = "services"
    services.Parent = npcSystem
    
    return true
end

-- Wait for required services to be ready
local function waitForServices()
    local maxAttempts = 10
    local attempts = 0
    
    while attempts < maxAttempts do
        if ensureRequiredServices() then
            return true
        end
        attempts = attempts + 1
        task.wait(0.5)
    end
    
    error("Failed to initialize required services")
end

-- Initialize system
local function init()
    if not waitForServices() then
        error("Failed to initialize NPC system - required services not found")
        return
    end
    
    -- Load NPCManagerV3
    local NPCManagerV3 = require(ReplicatedStorage.Shared.NPCSystem.NPCManagerV3)
    NPCManagerV3:init()
end

init() 