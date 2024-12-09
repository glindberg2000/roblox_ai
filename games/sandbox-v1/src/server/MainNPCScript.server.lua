-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local Logger = require(ServerScriptService:WaitForChild("Logger"))

local success, result = pcall(function()
	return require(ServerScriptService:WaitForChild("InteractionController", 5))
end)

if success then
	InteractionController = result
	Logger:log("SYSTEM", "InteractionController loaded successfully")
else
	Logger:log("ERROR", "Failed to load InteractionController: " .. tostring(result))
	-- Provide a basic implementation to prevent further errors
	InteractionController = {
		new = function()
			return {
				canInteract = function()
					return true
				end,
				startInteraction = function()
					return true
				end,
				endInteraction = function() end,
				getInteractingNPC = function()
					return nil
				end,
			}
		end,
	}
end

-- Rest of your MainNPCScript code...
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")

local Logger = require(ServerScriptService:WaitForChild("Logger"))

-- Move ensureStorage to the top, before NPC initialization
local function ensureStorage()
    local ServerStorage = game:GetService("ServerStorage")
    
    -- Create Assets/npcs folder structure
    local Assets = ServerStorage:FindFirstChild("Assets") or 
                   Instance.new("Folder", ServerStorage)
    Assets.Name = "Assets"
    
    local npcs = Assets:FindFirstChild("npcs") or 
                 Instance.new("Folder", Assets)
    npcs.Name = "npcs"
    
    Logger:log("SYSTEM", "Storage structure verified")
end

-- Call ensureStorage first
ensureStorage()

-- Add near the top with other constants
local ANIMATIONS = {
    -- Basic locomotion
    WALK = "rbxassetid://180426354",
    IDLE = "rbxassetid://180435571",
    RUN = "rbxassetid://180426354",
    JUMP = "rbxassetid://125750702",
    
    -- Emotes
    WAVE = "rbxassetid://507770239",
    DANCE = "rbxassetid://507771019",
    LAUGH = "rbxassetid://507770818",
    POINT = "rbxassetid://507770453",
}

-- Modify loadAnimations to support more animations
local function loadAnimations(npc)
    if not npc.model or not npc.model:FindFirstChild("Humanoid") then 
        Logger:log("ERROR", string.format("Cannot load animations for %s - missing model or humanoid", npc.displayName))
        return 
    end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    local animator = humanoid:FindFirstChild("Animator") or Instance.new("Animator", humanoid)
    
    -- Create animation objects
    npc.animTracks = {}
    
    -- Load all animations
    for name, id in pairs(ANIMATIONS) do
        local anim = Instance.new("Animation")
        anim.AnimationId = id
        
        local success, track = pcall(function()
            return animator:LoadAnimation(anim)
        end)
        
        if success then
            npc.animTracks[name:lower()] = track
            Logger:log("DEBUG", string.format("Loaded animation '%s' for %s", name, npc.displayName))
        else
            Logger:log("ERROR", string.format("Failed to load animation '%s' for %s", name, npc.displayName))
        end
    end
    
    -- Start with idle
    if npc.animTracks.idle then
        npc.animTracks.idle:Play()
    end
end

-- Add animation control function
local function playAnimation(npc, animName, options)
    options = options or {}
    
    if not npc.animTracks then return end
    
    -- Convert to lowercase for consistency
    animName = animName:lower()
    
    -- Get the requested animation track
    local track = npc.animTracks[animName]
    if not track then
        Logger:log("ERROR", string.format("Animation '%s' not found for %s", animName, npc.displayName))
        return
    end
    
    -- Stop other animations unless specified not to
    if not options.keepOthers then
        for name, otherTrack in pairs(npc.animTracks) do
            if name ~= animName then
                otherTrack:Stop()
            end
        end
    end
    
    -- Play the animation
    if not track.IsPlaying then
        track:Play()
        
        -- Handle one-shot animations
        if options.oneShot then
            track.Stopped:Wait()
            -- Return to idle
            if npc.animTracks.idle then
                npc.animTracks.idle:Play()
            end
        end
    end
end

-- Add function to handle animation actions from LLM
local function handleAnimationAction(npc, action)
    if not action or not action.type then return end
    
    if action.type == "animate" then
        local animName = action.animation
        local options = {
            oneShot = action.oneShot,
            keepOthers = action.keepOthers
        }
        
        -- Handle the animation in a new thread if it's one-shot
        if options.oneShot then
            spawn(function()
                playAnimation(npc, animName, options)
            end)
        else
            playAnimation(npc, animName, options)
        end
    end
end

-- Then initialize NPC system
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))
Logger:log("SYSTEM", "Starting NPC initialization")
local npcManagerV3 = NPCManagerV3.new()

-- Load animations after NPCs are created
for _, npc in pairs(npcManagerV3.npcs) do
    if npc.model then
        -- Log model state
        Logger:log("DEBUG", string.format("[MODEL] %s model state: %s", 
            npc.displayName,
            npc.model.Parent and "Loaded" or "Not in workspace"
        ))
        
        -- Wait a short time for model to fully load
        wait(0.1)
        loadAnimations(npc)
    else
        Logger:log("ERROR", string.format("[MODEL] %s has no model", npc.displayName))
    end
end

-- Debug NPC abilities
for npcId, npcData in pairs(npcManagerV3.npcs) do
	Logger:log("DEBUG", string.format("NPC %s abilities: %s", 
		npcData.displayName,
		table.concat(npcData.abilities or {}, ", ")
	))
end

for npcId, npcData in pairs(npcManagerV3.npcs) do
	Logger:log("STATE", string.format("NPC spawned: %s", npcData.displayName))
end

local interactionController = npcManagerV3.interactionController

Logger:log("SYSTEM", "NPC system V3 initialized")

-- Add cooldown tracking
local greetingCooldowns = {}
local GREETING_COOLDOWN = 30 -- seconds between greetings

-- Add at the top with other state variables
local activeConversations = {
    playerToNPC = {}, -- player UserId -> npcId
    npcToNPC = {},    -- npc Id -> npc Id
    npcToPlayer = {}  -- npc Id -> player UserId
}

local function checkPlayerProximity()
    for _, player in ipairs(Players:GetPlayers()) do
        local playerPosition = player.Character and player.Character.PrimaryPart
        if playerPosition then
            for _, npc in pairs(npcManagerV3.npcs) do
                if npc.model and npc.model.PrimaryPart then
                    local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
                    local isInRange = distance <= npc.responseRadius

                    -- Log range check for debugging
                    Logger:log("RANGE", string.format(
                        "[PLAYER] Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                        player.Name,
                        npc.displayName,
                        distance,
                        npc.responseRadius,
                        tostring(isInRange)
                    ))

                    -- Only proceed if in range and NPC isn't busy
                    if isInRange and not npc.isInteracting and not activeConversations.npcToPlayer[npc.id] then
                        -- Check if NPC has initiate_chat ability
                        local hasInitiateAbility = false
                        for _, ability in ipairs(npc.abilities or {}) do
                            if ability == "initiate_chat" then
                                hasInitiateAbility = true
                                break
                            end
                        end

                        if hasInitiateAbility and interactionController:canInteract(player) then
                            -- Check cooldown
                            local cooldownKey = npc.id .. "_" .. player.UserId
                            local lastGreeting = greetingCooldowns[cooldownKey]
                            if lastGreeting then
                                local timeSinceLastGreeting = os.time() - lastGreeting
                                if timeSinceLastGreeting < GREETING_COOLDOWN then continue end
                            end

                            Logger:log("DEBUG", string.format("NPC initiating chat: %s -> %s", 
                                npc.displayName, player.Name))

                            -- Lock conversation
                            activeConversations.npcToPlayer[npc.id] = player.UserId
                            activeConversations.playerToNPC[player.UserId] = npc.id

                            -- Send system message about player in range
                            local systemMessage = string.format(
                                "[SYSTEM] A player (%s) has entered your area. You can initiate a conversation if you'd like.",
                                player.Name
                            )
                            npcManagerV3:handleNPCInteraction(npc, player, systemMessage)
                            greetingCooldowns[cooldownKey] = os.time()
                        end
                    end
                end
            end
        end
    end
end

local function onPlayerChatted(player, message)
    -- Get player position
    local playerPosition = player.Character and player.Character.PrimaryPart
    if not playerPosition then return end

    -- Find closest NPC in range
    local closestNPC, closestDistance = nil, math.huge

    for _, npc in pairs(npcManagerV3.npcs) do
        if npc.model and npc.model.PrimaryPart then
            local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
            
            -- Log range check for debugging
            Logger:log("RANGE", string.format(
                "Distance between player %s and NPC %s: %.2f studs (Radius: %d, InRange: %s)",
                player.Name,
                npc.displayName,
                distance,
                npc.responseRadius,
                tostring(distance <= npc.responseRadius)
            ))

            -- Only consider NPCs in range and not already interacting
            if distance <= npc.responseRadius and distance < closestDistance and not npc.isInteracting then
                closestNPC, closestDistance = npc, distance
            end
        end
    end

    if closestNPC then
        local cooldownKey = closestNPC.id .. "_" .. player.UserId
        local lastGreeting = greetingCooldowns[cooldownKey]
        local isGreeting = message:lower():match("^h[ae][yl]l?o+!?$") or message:lower() == "hi"
        
        if isGreeting and lastGreeting then
            local timeSinceLastGreeting = os.time() - lastGreeting
            if timeSinceLastGreeting < GREETING_COOLDOWN then
                Logger:log("DEBUG", string.format(
                    "Skipping player greeting - on cooldown for %d more seconds",
                    GREETING_COOLDOWN - timeSinceLastGreeting
                ))
                return
            end
        end

        Logger:log("INTERACTION", string.format("Routing chat from %s to NPC %s (Distance: %.2f)", 
            player.Name, closestNPC.displayName, closestDistance))
        npcManagerV3:handleNPCInteraction(closestNPC, player, message)
        
        if isGreeting then
            greetingCooldowns[cooldownKey] = os.time()
        end
    else
        Logger:log("INTERACTION", string.format(
            "No NPCs in range for player %s chat", 
            player.Name
        ))
    end
end

local function setupChatConnections()
	Logger:log("SYSTEM", "Setting up chat connections")
	Players.PlayerAdded:Connect(function(player)
		Logger:log("STATE", string.format("Setting up chat connection for player: %s", player.Name))
		player.Chatted:Connect(function(message)
			onPlayerChatted(player, message)
		end)
	end)
end

setupChatConnections()

local function checkNPCProximity()
    for _, npc1 in pairs(npcManagerV3.npcs) do
        -- Skip if no initiate_chat
        local hasInitiateAbility = false
        for _, ability in ipairs(npc1.abilities or {}) do
            if ability == "initiate_chat" then
                hasInitiateAbility = true
                break
            end
        end
        if not hasInitiateAbility then continue end

        -- Scan for other NPCs in range
        for _, npc2 in pairs(npcManagerV3.npcs) do
            if npc1 == npc2 or npc2.isInteracting then continue end
            if not npc2.model or not npc2.model.PrimaryPart then continue end

            local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
            local isInRange = distance <= npc1.responseRadius
            
            Logger:log("RANGE", string.format(
                "Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                npc1.displayName,
                npc2.displayName,
                distance,
                npc1.responseRadius,
                tostring(isInRange)
            ))

            -- Only proceed if in range and not already in conversation
            if not isInRange then continue end
            if activeConversations.npcToNPC[npc1.id] then continue end
            if activeConversations.npcToNPC[npc2.id] then continue end

            -- Check cooldown
            local cooldownKey = npc1.id .. "_" .. npc2.id
            local lastGreeting = greetingCooldowns[cooldownKey]
            if lastGreeting then
                local timeSinceLastGreeting = os.time() - lastGreeting
                if timeSinceLastGreeting < GREETING_COOLDOWN then continue end
            end

            Logger:log("INTERACTION", string.format("%s sees %s and can initiate chat", 
                npc1.displayName, npc2.displayName))
            
            -- Lock conversation
            activeConversations.npcToNPC[npc1.id] = {partner = npc2}
            activeConversations.npcToNPC[npc2.id] = {partner = npc1}
            
            -- Create mock participant and initiate
            local mockParticipant = npcManagerV3:createMockParticipant(npc2)
            local systemMessage = string.format(
                "[SYSTEM] Another NPC (%s) has entered your area. You can initiate a conversation if you'd like.",
                npc2.displayName
            )
            npcManagerV3:handleNPCInteraction(npc1, mockParticipant, systemMessage)
            greetingCooldowns[cooldownKey] = os.time()
        end
    end
end

local function checkOngoingConversations()
    for npc1Id, conversationData in pairs(activeConversations.npcToNPC) do
        local npc1 = npcManagerV3.npcs[npc1Id]
        local npc2 = conversationData.partner
        
        if npc1 and npc2 and npc1.model and npc2.model then
            local distance = (npc1.model.PrimaryPart.Position - npc2.model.PrimaryPart.Position).Magnitude
            local isInRange = distance <= npc1.responseRadius
            
            Logger:log("RANGE", string.format(
                "[ONGOING] Distance between %s and %s: %.2f studs (Radius: %d, InRange: %s)",
                npc1.displayName,
                npc2.displayName,
                distance,
                npc1.responseRadius,
                tostring(isInRange)
            ))

            if not isInRange then
                Logger:log("INTERACTION", string.format(
                    "Ending conversation - NPCs out of range (%s <-> %s)",
                    npc1.displayName,
                    npc2.displayName
                ))
                npcManagerV3:endInteraction(npc1, npc2)
            end
        end
    end
end

-- Add near the top with other functions
local function getRandomPosition(origin, radius)
    local angle = math.random() * math.pi * 2
    local distance = math.random() * radius
    return Vector3.new(
        origin.X + math.cos(angle) * distance,
        origin.Y,
        origin.Z + math.sin(angle) * distance
    )
end

local function moveNPC(npc, targetPosition)
    if not npc.model or not npc.model.PrimaryPart or not npc.model:FindFirstChild("Humanoid") then return end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    
    -- Play walk animation
    if npc.animTracks and npc.animTracks.walk then
        npc.animTracks.walk:Play()
    end
    
    humanoid:MoveTo(targetPosition)
    
    -- Switch to idle when done moving
    humanoid.MoveToFinished:Wait()
    
    if npc.animTracks then
        if npc.animTracks.walk then
            npc.animTracks.walk:Stop()
        end
        if npc.animTracks.idle then
            npc.animTracks.idle:Play()
        end
    end
end

local function updateNPCMovement()
    while true do
        for _, npc in pairs(npcManagerV3.npcs) do
            -- Check if NPC can move and isn't busy
            local canMove = false
            for _, ability in ipairs(npc.abilities or {}) do
                if ability == "move" then
                    canMove = true
                    break
                end
            end

            if canMove and not npc.isInteracting and 
               not activeConversations.npcToNPC[npc.id] and 
               not activeConversations.npcToPlayer[npc.id] then
                
                -- Random chance to start moving
                if math.random() < 0.8 then -- 80% chance each update
                    local spawnPos = npc.spawnPosition or npc.model.PrimaryPart.Position
                    local targetPos = getRandomPosition(spawnPos, 10) -- 10 stud radius
                    
                    Logger:log("MOVEMENT", string.format(
                        "Moving %s to random position (%.1f, %.1f, %.1f)",
                        npc.displayName,
                        targetPos.X,
                        targetPos.Y,
                        targetPos.Z
                    ))
                    
                    moveNPC(npc, targetPos)
                end
            end
        end
        wait(5) -- Check every 5 seconds
    end
end

-- Add to the main update loop
local function updateNPCs()
    Logger:log("SYSTEM", "Starting NPC update loop")
    spawn(updateNPCMovement) -- Start movement system in parallel
    while true do
        checkPlayerProximity()
        checkNPCProximity()
        checkOngoingConversations()
        wait(1)
    end
end

spawn(updateNPCs)

-- Handle player-initiated interaction ending
local EndInteractionEvent = Instance.new("RemoteEvent")
EndInteractionEvent.Name = "EndInteractionEvent"
EndInteractionEvent.Parent = ReplicatedStorage

EndInteractionEvent.OnServerEvent:Connect(function(player)
	local interactingNPC = interactionController:getInteractingNPC(player)
	if interactingNPC then
		Logger:log("INTERACTION", string.format("Player %s manually ended interaction with %s", 
			player.Name, interactingNPC.displayName))
		npcManagerV3:endInteraction(interactingNPC, player)
	end
end)

Logger:log("SYSTEM", "NPC system V3 main script running")

-- In your interaction handler
local function handleNPCResponse(npc, response)
    -- Handle chat message
    if response.message then
        -- Existing chat handling...
    end
    
    -- Handle action if present
    if response.action then
        handleAnimationAction(npc, response.action)
    end
end
