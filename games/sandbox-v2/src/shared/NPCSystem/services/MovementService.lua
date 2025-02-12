-- MovementService.lua
local LoggerService = {
    debug = function(_, category, message) 
        print(string.format("[DEBUG] [%s] %s", category, message))
    end,
    warn = function(_, category, message)
        warn(string.format("[WARN] [%s] %s", category, message))
    end
}

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
        -- Cancel the follow thread
        task.cancel(self.followThreads[npc])
        self.followThreads[npc] = nil
        
        -- Stop the humanoid
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            local humanoid = npc.model:FindFirstChild("Humanoid")
            humanoid:MoveTo(npc.model.PrimaryPart.Position)
        end
        
        LoggerService:debug("MOVEMENT", string.format("Stopped following for %s", npc.displayName))
    end
end

function MovementService:moveNPCToPosition(npc, targetPosition)
    -- Validate input
    if not npc or not npc.model then
        LoggerService:warn("MOVEMENT", "Invalid NPC passed to moveNPCToPosition")
        return false
    end

    local humanoid = npc.model:FindFirstChild("Humanoid")
    local rootPart = npc.model:FindFirstChild("HumanoidRootPart")
    
    if not humanoid or not rootPart then
        LoggerService:warn("MOVEMENT", string.format(
            "Missing humanoid or rootPart for NPC %s",
            npc.model.Name
        ))
        return false
    end

    -- Calculate distance
    local distance = (targetPosition - rootPart.Position).Magnitude
    
    LoggerService:debug("MOVEMENT", string.format(
        "Moving NPC %s from (%0.1f, %0.1f, %0.1f) to (%0.1f, %0.1f, %0.1f) - Distance: %0.1f",
        npc.model.Name,
        rootPart.Position.X, rootPart.Position.Y, rootPart.Position.Z,
        targetPosition.X, targetPosition.Y, targetPosition.Z,
        distance
    ))

    -- Move to position
    humanoid:MoveTo(targetPosition)
    
    return true
end

function MovementService:getRandomPosition(origin, radius)
    -- Generate random angle
    local angle = math.random() * math.pi * 2
    
    -- Generate random distance within radius
    local distance = math.sqrt(math.random()) * radius
    
    -- Calculate offset
    local xOffset = math.cos(angle) * distance
    local zOffset = math.sin(angle) * distance
    
    -- Return new position
    return Vector3.new(
        origin.X + xOffset,
        origin.Y,
        origin.Z + zOffset
    )
end

return MovementService 