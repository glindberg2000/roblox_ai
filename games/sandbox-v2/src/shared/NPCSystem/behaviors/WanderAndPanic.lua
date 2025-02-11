local PathfindingService = game:GetService("PathfindingService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local LoggerService = require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
local MovementService = require(ReplicatedStorage.Shared.NPCSystem.services.MovementService).new()

local WanderAndPanic = {}

function WanderAndPanic.init(npc)
    LoggerService:debug("BEHAVIOR", string.format(
        "WanderAndPanic.init called for NPC %s",
        npc.Name
    ))

    -- Validate NPC model
    if not npc then
        LoggerService:error("BEHAVIOR", "No NPC model provided to WanderAndPanic.init")
        return
    end

    local humanoid = npc:FindFirstChild("Humanoid")
    if not humanoid then
        LoggerService:error("BEHAVIOR", string.format(
            "No Humanoid found in NPC %s",
            npc.Name
        ))
        return
    end

    local rootPart = npc:FindFirstChild("HumanoidRootPart")
    if not rootPart then
        LoggerService:error("BEHAVIOR", string.format(
            "No HumanoidRootPart found in NPC %s",
            npc.Name
        ))
        return
    end

    LoggerService:debug("BEHAVIOR", string.format(
        "Initializing wander behavior for %s with humanoid %s and rootPart %s",
        npc.Name,
        humanoid:GetFullName(),
        rootPart:GetFullName()
    ))

    -- Create a wrapper for the NPC to match MovementService expectations
    local npcWrapper = {
        model = npc,
        displayName = npc.Name
    }

    -- Start the wander coroutine
    coroutine.wrap(function()
        LoggerService:debug("BEHAVIOR", string.format(
            "Starting wander coroutine for NPC %s",
            npc.Name
        ))

        while task.wait(math.random(3, 6)) do
            LoggerService:debug("BEHAVIOR", string.format(
                "NPC %s starting wander cycle",
                npc.Name
            ))
            
            -- Get random position
            local rand1 = math.random(-40, 40)
            local rand2 = math.random(-40, 40)
            local targetPos = Vector3.new(
                rootPart.Position.X + rand1,
                rootPart.Position.Y,
                rootPart.Position.Z + rand2
            )

            LoggerService:debug("BEHAVIOR", string.format(
                "NPC %s attempting to path to (%.1f, %.1f, %.1f)",
                npc.Name,
                targetPos.X,
                targetPos.Y,
                targetPos.Z
            ))
            
            -- Create path
            local path = PathfindingService:CreatePath({
                AgentRadius = 2,
                AgentHeight = 5,
                AgentCanJump = true
            })
            
            local success, errorMessage = pcall(function()
                path:ComputeAsync(rootPart.Position, targetPos)
            end)
            
            if success and path.Status == Enum.PathStatus.Success then
                LoggerService:debug("BEHAVIOR", string.format(
                    "NPC %s found path with %d waypoints",
                    npc.Name,
                    #path:GetWaypoints()
                ))
                
                local waypoints = path:GetWaypoints()
                for i, waypoint in ipairs(waypoints) do
                    LoggerService:debug("BEHAVIOR", string.format(
                        "NPC %s moving to waypoint %d/%d at position (%.1f, %.1f, %.1f)",
                        npc.Name,
                        i,
                        #waypoints,
                        waypoint.Position.X,
                        waypoint.Position.Y,
                        waypoint.Position.Z
                    ))
                    MovementService:moveNPCToPosition(npcWrapper, waypoint.Position)
                    task.wait(0.5) -- Wait for movement
                end
            else
                LoggerService:warn("BEHAVIOR", string.format(
                    "Failed to compute path for %s: %s",
                    npc.Name,
                    errorMessage or "Unknown error"
                ))
            end
            
            task.wait(1) -- Wait before next wander
        end
    end)()

    LoggerService:debug("BEHAVIOR", string.format(
        "WanderAndPanic initialized for %s",
        npc.Name
    ))
end

return WanderAndPanic 