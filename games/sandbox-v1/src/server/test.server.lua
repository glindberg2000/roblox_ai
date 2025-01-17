local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function testSync()
    print("Testing sync...")
    
    -- Test Shared folder
    local shared = ReplicatedStorage:WaitForChild("Shared", 5)
    if shared then
        print("Found Shared folder")
        
        -- Test NPCSystem folder
        local npcSystem = shared:WaitForChild("NPCSystem", 5)
        if npcSystem then
            print("Found NPCSystem folder")
            
            -- Test services folder
            local services = npcSystem:WaitForChild("services", 5)
            if services then
                print("Found services folder")
                
                -- Try to load LoggerService
                local success, result = pcall(function()
                    return require(services.LoggerService)
                end)
                if success then
                    print("Successfully loaded LoggerService")
                else
                    warn("Failed to load LoggerService:", result)
                end
            end
        end
    end
end

testSync() 