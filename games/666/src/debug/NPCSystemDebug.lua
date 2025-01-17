local function findAllNPCScripts()
    local function searchInContainer(container, results)
        for _, item in ipairs(container:GetDescendants()) do
            if item:IsA("Script") and 
               (item.Name:find("NPC") or item.Name:find("npc")) then
                table.insert(results, item:GetFullName())
            end
        end
    end
    
    local results = {}
    searchInContainer(game:GetService("ServerScriptService"), results)
    searchInContainer(game:GetService("ReplicatedStorage"), results)
    
    print("=== Found NPC-related scripts ===")
    for _, path in ipairs(results) do
        print(path)
    end
    print("===============================")
end

return {
    findAllNPCScripts = findAllNPCScripts
} 