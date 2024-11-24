-- ScriptApplier.server.lua
local ServerStorage = game:GetService("ServerStorage")
local AnimateScript = require(ServerStorage.Assets.scripts.AnimateScript)
local WalkScript = require(ServerStorage.Assets.scripts.WalkScript)

local ScriptApplier = {}

-- Apply scripts and behaviors to an NPC
function ScriptApplier.applyScriptsToNPC(npcModel)
    print("[ScriptApplier] Applying scripts to NPC:", npcModel.Name)

    if not npcModel or not npcModel:IsA("Model") then
        warn("[ScriptApplier] Invalid NPC model. Skipping:", npcModel)
        return
    end

    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    if not humanoid then
        warn("[ScriptApplier] Humanoid not found in NPC model:", npcModel.Name)
        return
    end

    local walkScript = ServerStorage.Assets.scripts:FindFirstChild("WalkScript")
    if walkScript then
        if not npcModel:FindFirstChild("WalkScript") then
            local walkScriptClone = walkScript:Clone()
            walkScriptClone.Parent = npcModel
            print("[ScriptApplier] WalkScript applied to NPC:", npcModel.Name)
        end
    else
        warn("[ScriptApplier] WalkScript not found in Assets/scripts.")
    end
end

-- Apply scripts to all NPCs
function ScriptApplier.applyToAll(npcs)
    for npcId, npcData in pairs(npcs) do
        print("Applying scripts to NPC:", npcData.displayName)
        local success, err = pcall(function()
            ScriptApplier.applyScriptsToNPC(npcData.model)
        end)
        if not success then
            warn("Error applying scripts to NPC " .. npcData.displayName .. ": " .. tostring(err))
        end
    end
end

return ScriptApplier