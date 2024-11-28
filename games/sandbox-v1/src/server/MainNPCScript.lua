function updateNPCs()
    Logger:log("UPDATE", "------- Starting NPC State Update -------")
    
    for _, npc in pairs(NPCManager.npcs) do
        NPCManager:updateNPCState(npc)
    end
    
    Logger:log("UPDATE", "------- Finished NPC State Update -------")
    wait(UPDATE_INTERVAL)
end 