local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

-- Test function to run all checks
local function runTests()
    LoggerService:info("TEST", "Starting MockPlayer tests...")
    
    -- Test 1: Basic instantiation with type
    local testPlayer = MockPlayer.new("TestUser", 12345, "npc")
    assert(testPlayer ~= nil, "MockPlayer should be created successfully")
    assert(testPlayer.Name == "TestUser", "Name should match constructor argument")
    assert(testPlayer.DisplayName == "TestUser", "DisplayName should match Name")
    assert(testPlayer.UserId == 12345, "UserId should match constructor argument")
    assert(testPlayer.Type == "npc", "Type should be set to npc")
    LoggerService:info("TEST", "✓ Basic instantiation tests passed")
    
    -- Test 2: Default type behavior
    local defaultPlayer = MockPlayer.new("DefaultUser")
    assert(defaultPlayer.Type == "npc", "Default Type should be 'npc'")
    LoggerService:info("TEST", "✓ Default type test passed")
    
    -- Test 3: IsA functionality
    assert(testPlayer:IsA("Player") == true, "IsA('Player') should return true")
    LoggerService:info("TEST", "✓ IsA tests passed")
    
    -- Test 4: GetParticipantType functionality
    assert(testPlayer:GetParticipantType() == "npc", "GetParticipantType should return 'npc'")
    local playerTypeMock = MockPlayer.new("PlayerTest", 789, "player")
    assert(playerTypeMock:GetParticipantType() == "player", "GetParticipantType should return 'player'")
    LoggerService:info("TEST", "✓ GetParticipantType tests passed")
    
    LoggerService:info("TEST", "All MockPlayer tests passed successfully!")
end

-- Run tests in protected call to catch any errors
local success, error = pcall(runTests)
if not success then
    LoggerService:error("TEST", string.format("MockPlayer tests failed: %s", tostring(error)))
end 