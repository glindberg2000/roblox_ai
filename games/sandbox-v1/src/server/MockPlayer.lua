-- ServerScriptService/MockPlayer.lua
local MockPlayer = {}
MockPlayer.__index = MockPlayer

function MockPlayer.new(name, userId)
    local self = setmetatable({}, MockPlayer)
    self.Name = name
    self.DisplayName = name
    self.UserId = userId or -1  -- Negative ID to avoid conflicts
    return self
end

function MockPlayer:IsA(className)
    return className == "Player"
end

return MockPlayer