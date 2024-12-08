function runNPCInteractionTests()
    -- ... existing setup ...

    -- Test 1: Basic NPC-to-NPC interaction
    print("Test 1: Initiating basic NPC-to-NPC interaction")
    local mockParticipant = npcManager:createMockParticipant(npc1)
    
    -- Verify mock participant
    assert(mockParticipant.Type == "npc", "Mock participant should be of type 'npc'")
    assert(mockParticipant.model == npc1.model, "Mock participant should have correct model reference")
    assert(mockParticipant.npcId == npc1.id, "Mock participant should have correct NPC ID")
    
    -- Start interaction
    local success, err = pcall(function()
        npcManager:handleNPCInteraction(npc2, mockParticipant, "Hello!")
        wait(2) -- Wait for the interaction to process
        
        -- Verify states
        assert(npc2.isInteracting, "NPC2 should be in interaction state")
        assert(npc2.model.Humanoid.WalkSpeed == 0, "NPC2 should be locked in place")
        
        -- Check for response
        assert(#npc2.chatHistory > 0, "NPC2 should have responded")
        print("NPC2 response: " .. npc2.chatHistory[#npc2.chatHistory])
    end)
    
    if not success then
        error("Interaction test failed: " .. tostring(err))
    end
    
    -- Clean up
    npcManager:endInteraction(npc2, mockParticipant)
    wait(1)
    
    -- Verify cleanup
    assert(not npc2.isInteracting, "NPC2 should not be in interaction state")
    assert(npc2.model.Humanoid.WalkSpeed > 0, "NPC2 should be unlocked")

    print("All NPC-to-NPC interaction tests passed!")
end 