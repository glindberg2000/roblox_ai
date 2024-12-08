local function createMockParticipant(npc)
    return {
        Name = npc.displayName,
        displayName = npc.displayName,
        UserId = npc.id,
        npcId = npc.id,
        Type = "npc"
    }
end

function NPCInteractionTest:testBasicInteraction()
    print("Test 1: Initiating basic NPC-to-NPC interaction")
    
    local npc1 = self.npcManager:getNPCByName("Goldie")
    local npc2 = self.npcManager:getNPCByName("Pete")
    
    local mockParticipant = self.npcManager:createMockParticipant(npc2)
    assert(mockParticipant, "Mock participant should have been created")
    
    -- Initialize chat service
    local ChatService = game:GetService("Chat")
    local success = pcall(function()
        ChatService:SetBubbleChatSettings({
            BubbleDuration = 10,
            MaxDistance = 80
        })
    end)
    print("Chat service initialized:", success)
    
    -- Test interaction
    print("Starting interaction between", npc1.displayName, "and", npc2.displayName)
    local response = self.npcManager:handleNPCInteraction(npc1, mockParticipant, "Hello!")
    
    -- Verify response
    assert(response, "Should have received a response")
    print("Got response:", response.message)
    
    -- Wait for chat bubble
    wait(1)
    
    return true
end 