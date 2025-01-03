-- ServerScriptService/InteractionController.lua
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Wait for critical paths
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local services = NPCSystem:WaitForChild("services")

local LoggerService = require(services.LoggerService)
local InteractionService = require(services.InteractionService)

local InteractionController = {}
InteractionController.__index = InteractionController

function InteractionController.new()
    local self = setmetatable({}, InteractionController)
    self.activeInteractions = {}
    LoggerService:log("SYSTEM", "InteractionController initialized")
    return self
end

function InteractionController:startInteraction(player, npc)
    if self.activeInteractions[player] then
        LoggerService:log("PLAYER", string.format("Player %s already in interaction", player.Name))
        return false
    end
    self.activeInteractions[player] = {npc = npc, startTime = tick()}
    LoggerService:log("PLAYER", string.format("Started interaction: %s with %s", player.Name, npc.displayName))
    return true
end

function InteractionController:endInteraction(player)
    LoggerService:log("PLAYER", string.format("Ending interaction for player %s", player.Name))
    self.activeInteractions[player] = nil
end

function InteractionController:canInteract(player)
    return not self.activeInteractions[player]
end

function InteractionController:getInteractingNPC(player)
    local interaction = self.activeInteractions[player]
    return interaction and interaction.npc or nil
end

function InteractionController:getInteractionState(player)
    local interaction = self.activeInteractions[player]
    if interaction then
        return {
            npc_id = interaction.npc.id,
            npc_name = interaction.npc.displayName,
            start_time = interaction.startTime,
            duration = tick() - interaction.startTime,
        }
    end
    return nil
end

function InteractionController:startGroupInteraction(players, npc)
    for _, player in ipairs(players) do
        self.activeInteractions[player] = {npc = npc, group = players, startTime = tick()}
    end
    LoggerService:log("PLAYER", string.format("Started group interaction with %d players", #players))
end

function InteractionController:isInGroupInteraction(player)
    local interaction = self.activeInteractions[player]
    return interaction and interaction.group ~= nil
end

function InteractionController:getGroupParticipants(player)
    local interaction = self.activeInteractions[player]
    if interaction and interaction.group then
        return interaction.group
    end
    return {player}
end

return InteractionController