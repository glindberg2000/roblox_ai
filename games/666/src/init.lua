local NPCSpawningService = require(script.Parent.services.NPCSpawningService)

-- More aggressive cleanup of existing NPC systems
local function cleanupExistingNPCSystems()
    local ServerScriptService = game:GetService("ServerScriptService")
    
    -- Keywords that indicate NPC-related scripts
    local npcKeywords = {
        "NPC",
        "npc",
        "Character",
        "character",
        "Spawn",
        "spawn"
    }
    
    -- Search and disable conflicting scripts
    for _, instance in ipairs(ServerScriptService:GetDescendants()) do
        if instance:IsA("Script") or instance:IsA("LocalScript") then
            for _, keyword in ipairs(npcKeywords) do
                if instance.Name:find(keyword) then
                    instance.Disabled = true
                    print("Disabled conflicting script:", instance:GetFullName())
                    break
                end
            end
        end
    end
    
    -- Clean up existing NPC folders
    local oldNPCFolders = {"NPCs", "Characters", "Actors", "AICharacters"}
    for _, folderName in ipairs(oldNPCFolders) do
        local folder = workspace:FindFirstChild(folderName)
        if folder and folder.Name ~= "NPCs" then
            folder:Destroy()
            print("Removed old NPC folder:", folderName)
        end
    end
end

-- Enable debug output
game:GetService("LogService").MessageOut:Connect(function(message, messageType)
    if messageType == Enum.MessageType.Warning then
        print("NPC Warning:", message)
    end
end)

print("=== Starting NPC System ===")
cleanupExistingNPCSystems()
NPCSpawningService:Initialize() 