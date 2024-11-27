-- ServerScriptService/MockPlayer.lua
local MockPlayer = {}
MockPlayer.__index = MockPlayer

function MockPlayer.new(name, userId, participantType)
    local self = setmetatable({}, MockPlayer)
    self.Name = name
    self.DisplayName = name
    self.UserId = userId or -1  -- Keep negative ID for backwards compatibility
    self.Type = participantType or "npc"  -- Default to "npc" if not specified
    return self
end

function MockPlayer:IsA(className)
    return className == "Player"
end

-- Add helper method to check participant type
function MockPlayer:GetParticipantType()
    return self.Type
end

return MockPlayer