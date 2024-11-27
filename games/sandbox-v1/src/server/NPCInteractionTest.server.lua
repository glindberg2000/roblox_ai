local ReplicatedStorage = game:GetService("ReplicatedStorage")
local NPCManagerV3 = require(ReplicatedStorage.NPCManagerV3)

local function runNPCInteractionTests()
    print("Starting NPC-to-NPC interaction tests...")
    
    -- Get the singleton instance
    local npcManager = NPCManagerV3.new()
    
    -- Wait longer for NPCs to load from main initialization
    wait(5)
    
    -- Get two NPCs from the manager
    local npc1, npc2
    local npcCount = 0
    for id, npc in pairs(npcManager.npcs) do
        npcCount = npcCount + 1
        if npcCount == 1 then
            npc1 = npc
        elseif npcCount == 2 then
            npc2 = npc
            break
        end
    end
    
    if not (npc1 and npc2) then
        warn("Failed to find two NPCs for testing")
        return
    end
    
    -- Disable movement for both NPCs during test
    npc1.isMoving = false
    npc2.isMoving = false
    
    print(string.format("Testing interaction between %s and %s", npc1.displayName, npc2.displayName))
    
    -- Test 1: Basic NPC-to-NPC interaction
    print("Test 1: Initiating basic NPC-to-NPC interaction")
    local mockParticipant = npcManager:createMockParticipant(npc1)
    
    -- Verify mock participant
    assert(mockParticipant.Type == "npc", "Mock participant should be of type 'npc'")
    assert(mockParticipant.model == npc1.model, "Mock participant should have correct model reference")
    
    -- Start interaction
    local success, err = pcall(function()
        npcManager:handleNPCInteraction(npc2, mockParticipant, "Hello!")
        wait(1) -- Wait for interaction to process
        
        -- Verify interaction states
        assert(npc2.isInteracting, "NPC2 should be in interaction state")
        assert(not npc2.isMoving, "NPC2 should not be moving during interaction")
    end)
    
    if not success then
        error("Interaction test failed: " .. tostring(err))
    end
    
    print("✓ Basic interaction test passed")
    
    -- Clean up
    npcManager:endInteraction(npc2, mockParticipant)
    wait(1)
    
    -- Re-enable movement
    npc1.isMoving = true
    npc2.isMoving = true
    
    -- Test 1: Basic NPC-to-NPC interaction with movement locking
    print("Test 1: Testing NPC-to-NPC interaction with movement locking")
    local mockParticipant = npcManager:createMockParticipant(npc1)
    
    -- Start interaction
    local success, err = pcall(function()
        -- Verify initial states
        assert(npc1.isMoving == true, "NPC1 should be able to move initially")
        assert(npc2.isMoving == true, "NPC2 should be able to move initially")
        
        npcManager:handleNPCInteraction(npc2, mockParticipant, "Hello!")
        wait(1)
        
        -- Verify interaction states
        assert(npc2.isInteracting == true, "NPC2 should be in interaction state")
        assert(npc2.isMoving == false, "NPC2 should not be moving during interaction")
        assert(npc2.model.Humanoid.WalkSpeed == 0, "NPC2 walk speed should be 0")
        
        -- Get original NPC1 and verify its state
        local originalNPC1 = npcManager.npcs[tonumber(mockParticipant.UserId)]
        assert(originalNPC1.isMoving == false, "Original NPC1 should not be moving")
    end)
    
    if not success then
        error("Movement locking test failed: " .. tostring(err))
    end
    
    -- Test cleanup
    npcManager:endInteraction(npc2, mockParticipant)
    wait(1)
    
    -- Verify cleanup
    assert(npc2.isInteracting == false, "NPC2 should not be in interaction state after cleanup")
    assert(npc2.isMoving == true, "NPC2 should be able to move after cleanup")
    assert(npc2.model.Humanoid.WalkSpeed > 0, "NPC2 walk speed should be restored")
    
    print("All NPC interaction tests completed successfully!")
end

-- Run the tests in protected call
local success, error = pcall(function()
    runNPCInteractionTests()
end)

if not success then
    warn("NPC interaction tests failed: " .. tostring(error))
end 