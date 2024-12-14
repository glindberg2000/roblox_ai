-- MovementService.lua
local LoggerService = require(game.ReplicatedStorage.Shared.LoggerService)

local MovementService = {}
MovementService.__index = MovementService

function MovementService.new()
    local self = setmetatable({}, MovementService)
    self.followThreads = {}
    LoggerService:debug("MOVEMENT", "New MovementService instance created")
    return self
end

function MovementService:startFollowing(npc, target, options)
    LoggerService:debug("MOVEMENT", string.format(
        "Starting follow behavior - NPC: %s, Target: %s",
        npc.displayName,
        target.Name
    ))

    local followDistance = options and options.distance or 5
    local updateRate = options and options.updateRate or 0.1

    -- Clean up existing thread if any
    self:stopFollowing(npc)

    -- Create new follow thread
    local thread = task.spawn(function()
        while true do
            if not npc.model or not target then break end
            
            local npcRoot = npc.model:FindFirstChild("HumanoidRootPart")
            local targetRoot = target:FindFirstChild("HumanoidRootPart")
            
            if npcRoot and targetRoot then
                local distance = (npcRoot.Position - targetRoot.Position).Magnitude
                
                if distance > followDistance then
                    local humanoid = npc.model:FindFirstChild("Humanoid")
                    if humanoid then
                        -- Set appropriate walk speed
                        humanoid.WalkSpeed = distance > 20 and 16 or 8
                        humanoid:MoveTo(targetRoot.Position)
                    end
                end
            end
            
            task.wait(updateRate)
        end
    end)

    -- Store thread reference
    self.followThreads[npc] = thread
end

function MovementService:stopFollowing(npc)
    if self.followThreads[npc] then
        task.cancel(self.followThreads[npc])
        self.followThreads[npc] = nil
        LoggerService:debug("MOVEMENT", string.format("Stopped following for %s", npc.displayName))
    end
end

function MovementService:moveNPCToPosition(npc, targetPosition)
    if not npc or not npc.model then return end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then return end
    
    -- Get current position
    local currentPosition = npc.model:GetPrimaryPartCFrame().Position
    local distance = (targetPosition - currentPosition).Magnitude
    
    -- Set appropriate walk speed
    if distance > 20 then
        humanoid.WalkSpeed = 16  -- Run speed
    else
        humanoid.WalkSpeed = 8   -- Walk speed
    end
    
    -- Move to position
    humanoid:MoveTo(targetPosition)
end

function MovementService:getRandomPosition(center, radius)
    local angle = math.random() * math.pi * 2
    local distance = math.sqrt(math.random()) * radius
    
    return Vector3.new(
        center.X + math.cos(angle) * distance,
        center.Y,
        center.Z + math.sin(angle) * distance
    )
end

return MovementService 