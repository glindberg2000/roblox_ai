-- ServerScriptService/InteractionController.lua

local InteractionController = {}
InteractionController.__index = InteractionController

function InteractionController.new()
    local self = setmetatable({}, InteractionController)
    self.activeInteractions = {}
    return self
end

function InteractionController:startInteraction(player, npc)
    if self.activeInteractions[player] then
        return false
    end
    self.activeInteractions[player] = {npc = npc, startTime = tick()}
    return true
end

function InteractionController:endInteraction(player)
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