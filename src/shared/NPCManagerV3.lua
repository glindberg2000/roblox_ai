local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local AnimationManager = require(ReplicatedStorage.Shared.AnimationManager)
local Logger = require(game:GetService("ServerScriptService"):WaitForChild("Logger"))

function NPCManagerV3:updateNPCVision(npc)
    Logger:log("Updating vision for " .. npc.displayName, Logger.LOG_TYPES.VISION)
    npc.visibleEntities = {}
    local npcPosition = npc.model.PrimaryPart.Position

    -- Detect players
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "player",
                    name = player.Name,
                    distance = distance,
                })
                Logger:log(npc.displayName .. " sees player: " .. player.Name .. " at distance: " .. distance, Logger.LOG_TYPES.VISION)
            end
        end
    end
    -- ... rest of the function
end

function NPCManagerV3:startFollowing(npc, player)
    Logger:log(string.format("%s starting to follow %s", npc.displayName, player.Name), Logger.LOG_TYPES.MOVEMENT)
    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()

    -- Play walk animation
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        AnimationManager:playAnimation(humanoid, "walk")
    end
    
    Logger:log(
        string.format(
            "Follow state set for %s: isFollowing=%s, followTarget=%s",
            npc.displayName,
            tostring(npc.isFollowing),
            player.Name
        ),
        Logger.LOG_TYPES.MOVEMENT
    )
end

function NPCManagerV3:handleNPCInteraction(npc, player, message)
    Logger:log(string.format("Interaction started between %s and %s", npc.displayName, player.Name), Logger.LOG_TYPES.INTERACTION)
    
    if self.interactionController:isInGroupInteraction(player) then
        self:handleGroupInteraction(npc, player, message)
        return
    end

    if not self.interactionController:canInteract(player) then
        local interactingNPC = self.interactionController:getInteractingNPC(player)
        if interactingNPC ~= npc then
            Logger:log("Player already interacting with different NPC", Logger.LOG_TYPES.INTERACTION)
            return
        end
    else
        if not self.interactionController:startInteraction(player, npc) then
            Logger:log("Failed to start interaction", Logger.LOG_TYPES.ERROR)
            return
        end
    end
    -- ... rest of the function
end

function NPCManagerV3:createNPC(npcData)
    if not npcData then
        Logger:error("Failed to create NPC: npcData is nil")
        return
    end
    
    Logger:log("Creating NPC: " .. npcData.displayName, Logger.LOG_TYPES.SYSTEM)
    -- ... rest of the function
end 