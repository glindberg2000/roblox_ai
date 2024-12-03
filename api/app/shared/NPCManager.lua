function NPCManager:HandleAutoInteraction(npc, participant)
    -- Check cooldown first
    local lastInteraction = self.interactionCooldowns[participant.UserId]
    if lastInteraction then
        local timeSinceLastInteraction = os.time() - lastInteraction
        if timeSinceLastInteraction < GREETING_COOLDOWN then
            print(f"[INTERACTION] Skipping duplicate greeting (cooldown: {GREETING_COOLDOWN - timeSinceLastInteraction} seconds)")
            return
        end
    end

    -- Rest of interaction code...
    self:StartInteraction(npc, participant)
    self.interactionCooldowns[participant.UserId] = os.time()
end

function NPCManager:HandleNPCChat(sourceNPC, targetNPC, message)
    local request = {
        message = message,
        npc_id = targetNPC.npc_id,
        participant_type = "npc",
        context = {
            participant_name = sourceNPC.display_name,
            participant_id = sourceNPC.npc_id,
            source_system_prompt = sourceNPC.system_prompt,
            is_npc_chat = true
        },
        system_prompt = targetNPC.system_prompt
    }

    local response = self.chatHandler:HandleChat(request)
    if response then
        self:ProcessResponse(targetNPC, response)
        if response.should_respond then
            self:HandleNPCChat(targetNPC, sourceNPC, response.message)
        end
    end
end

function NPCManager:Update()
    -- Existing update code...
    
    -- Handle NPC-to-NPC interactions
    for _, sourceNPC in pairs(self.npcs) do
        for _, targetNPC in pairs(self.npcs) do
            if sourceNPC ~= targetNPC and self:ShouldNPCsInteract(sourceNPC, targetNPC) then
                self:TriggerNPCInteraction(sourceNPC, targetNPC)
            end
        end
    end
end

function NPCManager:ShouldNPCsInteract(npc1, npc2)
    -- Check if NPCs are close enough
    local distance = (npc1.PrimaryPart.Position - npc2.PrimaryPart.Position).Magnitude
    if distance > NPC_INTERACTION_RANGE then return false end
    
    -- Check cooldown
    local key = npc1.npc_id .. npc2.npc_id
    local lastInteraction = self.npcInteractionCooldowns[key]
    if lastInteraction and os.time() - lastInteraction < NPC_CHAT_COOLDOWN then
        return false
    end
    
    return true
end

function NPCManager:TriggerNPCInteraction(sourceNPC, targetNPC)
    -- Start conversation with context
    local message = self:GenerateNPCGreeting(sourceNPC, targetNPC)
    self:HandleNPCChat(sourceNPC, targetNPC, message)
    
    -- Update cooldown
    local key = sourceNPC.npc_id .. targetNPC.npc_id
    self.npcInteractionCooldowns[key] = os.time()
end 