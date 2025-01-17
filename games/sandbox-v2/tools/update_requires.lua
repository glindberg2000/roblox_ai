local function scanFiles(directory)
    local oldPatterns = {
        'require%(ReplicatedStorage%.NPCSystem%.ChatUtils%)',
        'require%(ReplicatedStorage%.NPCSystem%.LettaConfig%)',
        'require%(ReplicatedStorage%.NPCSystem%.NPCChatHandler%)',
        'require%(ReplicatedStorage%.NPCSystem%.NPCConfig%)',
        'require%(ReplicatedStorage%.NPCSystem%.V3ChatClient%)',
        'require%(ReplicatedStorage%.NPCSystem%.V4ChatClient%)'
    }

    local newPaths = {
        'require(ReplicatedStorage.Shared.NPCSystem.chat.ChatUtils)',
        'require(ReplicatedStorage.Shared.NPCSystem.config.LettaConfig)',
        'require(ReplicatedStorage.Shared.NPCSystem.chat.NPCChatHandler)',
        'require(ReplicatedStorage.Shared.NPCSystem.config.NPCConfig)',
        'require(ReplicatedStorage.Shared.NPCSystem.chat.V3ChatClient)',
        'require(ReplicatedStorage.Shared.NPCSystem.chat.V4ChatClient)'
    }

    local findings = {}

    -- Scan directory recursively
    for _, file in ipairs(directory:GetDescendants()) do
        if file:IsA("ModuleScript") or file:IsA("Script") or file:IsA("LocalScript") then
            local source = file.Source
            for i, pattern in ipairs(oldPatterns) do
                if source:match(pattern) then
                    table.insert(findings, {
                        file = file:GetFullName(),
                        oldRequire = pattern,
                        newRequire = newPaths[i],
                        line = source:match(".*" .. pattern .. ".*")
                    })
                end
            end
        end
    end

    return findings
end

-- Print findings
local findings = scanFiles(game)
print("Files needing updates:")
for _, finding in ipairs(findings) do
    print("\nFile:", finding.file)
    print("Old:", finding.line)
    print("New:", finding.newRequire)
end 