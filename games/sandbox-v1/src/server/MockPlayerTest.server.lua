local ReplicatedStorage = game:GetService("ReplicatedStorage")
local MockPlayer = require(script.Parent.MockPlayer)

-- Test function to run all checks
local function runTests()
    print("Starting MockPlayer tests...")
    
    -- Test 1: Basic instantiation
    local testPlayer = MockPlayer.new("TestUser", 12345)
    assert(testPlayer ~= nil, "MockPlayer should be created successfully")
    assert(testPlayer.Name == "TestUser", "Name should match constructor argument")
    assert(testPlayer.DisplayName == "TestUser", "DisplayName should match Name")
    assert(testPlayer.UserId == 12345, "UserId should match constructor argument")
    print("✓ Basic instantiation tests passed")
    
    -- Test 2: IsA functionality
    assert(testPlayer:IsA("Player") == true, "IsA('Player') should return true")
    print("✓ IsA tests passed")
    
    -- Test 3: Default UserId behavior
    local defaultPlayer = MockPlayer.new("DefaultUser")
    assert(defaultPlayer.UserId < 0, "Default UserId should be negative")
    print("✓ Default UserId test passed")
    
    print("All MockPlayer tests passed successfully!")
end

-- Run tests in protected call to catch any errors
local success, error = pcall(runTests)
if not success then
    warn("MockPlayer tests failed: " .. tostring(error))
end 