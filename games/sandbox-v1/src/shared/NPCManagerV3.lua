-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local ChatService = game:GetService("Chat")

local AnimationManager = require(ReplicatedStorage.Shared.AnimationManager)
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))

-- Initialize Logger
local Logger
local function initializeLogger()
    local success, result = pcall(function()
        if game:GetService("RunService"):IsServer() then
            return require(ServerScriptService:WaitForChild("Logger"))
        else
            return require(ReplicatedStorage:WaitForChild("Logger"))
        end
    end)

    if success then
        Logger = result
        Logger:log("SYSTEM", "Logger initialized successfully")
    else
        -- Create a fallback logger with basic functionality
        Logger = {
            log = function(_, category, message)
                print(string.format("[%s] %s", category, message))
            end,
            error = function(_, message)
                warn("[ERROR] " .. message)
            end,
            warn = function(_, message)
                warn("[WARN] " .. message)
            end,
            debug = function(_, message)
                print("[DEBUG] " .. message)
            end
        }
        
        -- Log the initialization failure using the fallback logger
        Logger:error(string.format("Failed to initialize logger: %s. Using fallback logger.", tostring(result)))
    end

    -- Log the environment information
    local environment = game:GetService("RunService"):IsServer() and "Server" or "Client"
    Logger:log("SYSTEM", string.format("Running in %s environment", environment))
end

initializeLogger()
Logger:log("SYSTEM", "NPCManagerV3 module loaded")

local NPCManagerV3 = {}
NPCManagerV3.__index = NPCManagerV3

-- Add singleton instance variable
local instance = nil

function NPCManagerV3.getInstance()
    if not instance then
        instance = setmetatable({}, NPCManagerV3)
        instance.npcs = {}
        instance.responseCache = {}
        instance.interactionController = require(game.ServerScriptService.InteractionController).new()
        Logger:log("SYSTEM", "Initializing NPCManagerV3")
        instance:loadNPCDatabase()
    end
    return instance
end

-- Replace .new() with getInstance()
function NPCManagerV3.new()
    return NPCManagerV3.getInstance()
end

local API_URL = "https://roblox.ella-ai-care.com/robloxgpt/v3"
local RESPONSE_COOLDOWN = 1
local FOLLOW_DURATION = 60 -- Follow for 60 seconds by default
local MIN_FOLLOW_DISTANCE = 5 -- Minimum distance to keep from the player
local MEMORY_EXPIRATION = 3600 -- Remember players for 1 hour (in seconds)
local VISION_RANGE = 50 -- Range in studs for NPC vision

local NPC_RESPONSE_SCHEMA = {
	type = "object",
	properties = {
		message = { type = "string" },
		action = {
			type = "object",
			properties = {
				type = {
					type = "string",
					enum = { "follow", "unfollow", "stop_interacting", "none" },
				},
				data = { type = "object" },
			},
			required = { "type" },
			additionalProperties = false,
		},
		internal_state = { type = "object" },
	},
	required = { "message", "action" },
	additionalProperties = false,
}

local NPCChatEvent = ReplicatedStorage:FindFirstChild("NPCChatEvent") or Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

function NPCManagerV3:loadNPCDatabase()
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    Logger:log("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
    for _, npcData in ipairs(npcDatabase.npcs) do
        self:createNPC(npcData)
    end
end

function NPCManagerV3:createNPC(npcData)
    Logger:log("NPC", string.format("Creating NPC: %s", npcData.displayName))
    
    if not workspace:FindFirstChild("NPCs") then
        Instance.new("Folder", workspace).Name = "NPCs"
        Logger:log("SYSTEM", "Created NPCs folder in workspace")
    end

    local model = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
    if not model then
        Logger:log("ERROR", string.format("Model not found for NPC: %s", npcData.displayName))
        return
    end

    local npcModel = model:Clone()
    npcModel.Name = npcData.displayName
    npcModel.Parent = workspace.NPCs

    -- Check for necessary parts
    local humanoidRootPart = npcModel:FindFirstChild("HumanoidRootPart")
    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    local head = npcModel:FindFirstChild("Head")

    if not humanoidRootPart or not humanoid or not head then
        Logger:log("ERROR", string.format("NPC model %s is missing essential parts. Skipping creation.", npcData.displayName))
        npcModel:Destroy()
        return
    end

    -- Ensure the model has a PrimaryPart
    npcModel.PrimaryPart = humanoidRootPart

    -- Apply animations
    AnimationManager:applyAnimations(humanoid)

    local npc = {
        model = npcModel,
        id = npcData.id,
        displayName = npcData.displayName,
        responseRadius = npcData.responseRadius,
        system_prompt = npcData.system_prompt,
        lastResponseTime = 0,
        isMoving = false,
        isInteracting = false,
        isFollowing = false,
        followTarget = nil,
        followStartTime = 0,
        memory = {},
        visibleEntities = {},
        interactingPlayer = nil,
        shortTermMemory = {},
        chatHistory = {},
    }

    -- Position the NPC
    humanoidRootPart.CFrame = CFrame.new(npcData.spawnPosition)

    self:setupClickDetector(npc)
    self.npcs[npc.id] = npc
    Logger:log("NPC", string.format("NPC added: %s (Total NPCs: %d)", npc.displayName, self:getNPCCount()))
end

function NPCManagerV3:getNPCCount()
	local count = 0
	for _ in pairs(self.npcs) do
		count = count + 1
	end
	Logger:log("DEBUG", string.format("Current NPC count: %d", count))
	return count
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius

	-- Try to parent to HumanoidRootPart, if not available, use any BasePart
	local parent = npc.model:FindFirstChild("HumanoidRootPart") or npc.model:FindFirstChildWhichIsA("BasePart")

	if parent then
		clickDetector.Parent = parent
		Logger:log("INTERACTION", string.format("Set up ClickDetector for %s with radius %d", 
			npc.displayName, 
			npc.responseRadius
		))
	else
		Logger:log("ERROR", string.format("Could not find suitable part for ClickDetector on %s", npc.displayName))
		return
	end

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManagerV3:handleNPCInteraction(npc, participant, message)
    Logger:log("INTERACTION", string.format("Handling interaction: %s with %s - Message: %s",
        npc.displayName,
        participant.Name,
        message
    ))

    -- Lock NPCs in place if this is NPC-to-NPC interaction
    if self:isNPCParticipant(participant) then
        self:lockNPCInPlace(npc)
        local participantNPC = self.npcs[participant.npcId]
        if participantNPC then
            self:lockNPCInPlace(participantNPC)
        end
    end

    npc.isInteracting = true
    npc.interactingPlayer = participant

    local response = self:getResponseFromAI(npc, participant, message)
    if response then
        self:processAIResponse(npc, participant, response)
    else
        Logger:log("ERROR", string.format("Failed to get AI response for %s", npc.displayName))
        self:endInteraction(npc, participant)
    end
end

function NPCManagerV3:endInteraction(npc, participant)
    -- First unlock the initiating NPC
    self:unlockNPC(npc)
    
    -- Then unlock the target NPC if this was NPC-to-NPC
    if self:isNPCParticipant(participant) then
        local targetNPC = self.npcs[participant.npcId]
        if targetNPC then
            self:unlockNPC(targetNPC)
        end
    end

    -- Clear states
    npc.isInteracting = false
    npc.interactingPlayer = nil

    self.interactionController:endInteraction(participant)
    
    Logger:log("INTERACTION", string.format("Interaction ended between %s and %s", 
        npc.displayName, 
        participant.Name
    ))
end

function NPCManagerV3:getCacheKey(npc, player, message)
	local context = {
		npcId = npc.id,
		
		playerId = player.UserId,
		message = message,
		memory = npc.shortTermMemory[player.UserId],
	}
	
	local key = HttpService:JSONEncode(context)
	Logger:log("DEBUG", string.format("Generated cache key for %s and %s", npc.displayName, player.Name))
	return key
end

-- Require the Asset Database
local AssetDatabase = require(game.ServerScriptService.AssetDatabase)

-- Function to lookup asset data by name
local function getAssetData(assetName)
	for _, asset in ipairs(AssetDatabase.assets) do
		if asset.name == assetName then
			return asset
		end
	end
	return nil -- Return nil if the asset is not found
end

function NPCManagerV3:updateNPCVision(npc)
    npc.visibleEntities = {}
    local npcPosition = npc.model.PrimaryPart.Position

    -- First detect other NPCs
    for id, otherNPC in pairs(self.npcs) do
        if otherNPC ~= npc and otherNPC.model and otherNPC.model.PrimaryPart then
            local distance = (otherNPC.model.PrimaryPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "npc",
                    instance = otherNPC,
                    distance = distance,
                    name = otherNPC.displayName
                })
                Logger:log("VISION", string.format("%s sees NPC: %s at distance: %.2f",
                    npc.displayName,
                    otherNPC.displayName,
                    distance
                ))
            end
        end
    end

    -- Then detect players
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "player",
                    instance = player,
                    distance = distance,
                    name = player.Name
                })
                Logger:log("VISION", string.format("%s sees player: %s at distance: %.2f",
                    npc.displayName,
                    player.Name,
                    distance
                ))
            end
        end
    end
end

-- Update helper function to check if participant is NPC
function NPCManagerV3:isNPCParticipant(participant)
    return participant and (participant.Type == "npc" or participant.npcId ~= nil)
end

-- Update displayMessage function to handle both types
function NPCManagerV3:displayMessage(npc, message, recipient)
    -- First check if this is NPC-to-NPC chat
    if self:isNPCParticipant(recipient) then
        Logger:log("CHAT", string.format("NPC %s sending message to NPC %s: %s",
            npc.displayName,
            recipient.displayName,
            message
        ))
        
        -- Create a response from the recipient NPC
        local recipientNPC = self.npcs[recipient.npcId]
        if recipientNPC then
            local responderMock = self:createMockParticipant(npc)
            wait(1) -- Add small delay between messages
            self:handleNPCInteraction(recipientNPC, responderMock, message)
        end
        return
    end

    -- Handle player chat normally
    Logger:log("CHAT", string.format("NPC %s sending message to %s: %s",
        npc.displayName,
        recipient.Name,
        message
    ))

    -- Fire the chat event to the client
    NPCChatEvent:FireClient(recipient, {
        npcName = npc.displayName,
        message = message,
        type = "chat"
    })

    -- Record chat history
    table.insert(npc.chatHistory, {
        sender = npc.displayName,
        recipient = recipient.Name,
        message = message,
        timestamp = os.time()
    })
end

-- Update displayNPCToNPCMessage function
function NPCManagerV3:displayNPCToNPCMessage(fromNPC, toNPC, message)
    if not (fromNPC and toNPC and message) then
        Logger:log("ERROR", "Missing required parameters for NPC-to-NPC message")
        return
    end

    Logger:log("CHAT", string.format("NPC %s to NPC %s: %s", 
        fromNPC.displayName or "Unknown",
        toNPC.displayName or "Unknown",
        message
    ))
    
    -- Show chat bubble for NPC-to-NPC interactions
    if fromNPC.model and fromNPC.model:FindFirstChild("Head") then
        ChatService:Chat(fromNPC.model.Head, message, Enum.ChatColor.Blue)
    end
    
    -- Log the interaction
    Logger:log("NPC_CHAT", string.format("%s to %s: %s",
        fromNPC.displayName or "Unknown",
        toNPC.displayName or "Unknown",
        message
    ))
    
    -- Fire event to all clients so everyone can see NPC-to-NPC chat
    NPCChatEvent:FireAllClients(fromNPC.displayName, message)
end

function NPCManagerV3:executeAction(npc, player, action)
    Logger:log("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    if action.type == "stop_talking" then
        self:endInteraction(npc, player)
    elseif action.type == "follow" then
        Logger:log("MOVEMENT", string.format("Starting to follow player: %s", player.Name))
        self:startFollowing(npc, player)
    elseif action.type == "unfollow" then
        Logger:log("MOVEMENT", string.format("Stopping following player: %s", player.Name))
        self:stopFollowing(npc)
    elseif action.type == "emote" and action.data and action.data.emote then
        Logger:log("ANIMATION", string.format("Playing emote: %s", action.data.emote))
        self:playEmote(npc, action.data.emote)
    elseif action.type == "move" and action.data and action.data.position then
        Logger:log("MOVEMENT", string.format("Moving to position: %s", 
            tostring(action.data.position)
        ))
        self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
    elseif action.type == "none" then
        Logger:log("ACTION", "No action required")
    else
        Logger:log("ERROR", string.format("Unknown action type: %s", action.type))
    end
end

function NPCManagerV3:startFollowing(npc, player)
    Logger:log("MOVEMENT", string.format("%s starting to follow %s", npc.displayName, player.Name))
    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()

    -- Play walk animation
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        AnimationManager:playAnimation(humanoid, "walk")
    end
    
    Logger:log("STATE", string.format(
        "Follow state set for %s: isFollowing=%s, followTarget=%s",
        npc.displayName,
        tostring(npc.isFollowing),
        player.Name
    ))
end

function NPCManagerV3:updateInternalState(npc, internalState)
	Logger:log("STATE", string.format("Updating internal state for %s: %s",
		npc.displayName,
		HttpService:JSONEncode(internalState)
	))
	
	for key, value in pairs(internalState) do
		npc[key] = value
	end
end

function NPCManagerV3:playEmote(npc, emoteName)
    local Animator = npc.model:FindFirstChildOfClass("Animator")
    if Animator then
        local animation = ServerStorage.Animations:FindFirstChild(emoteName)
        if animation then
            Animator:LoadAnimation(animation):Play()
            Logger:log("ANIMATION", string.format("Playing emote %s for %s", emoteName, npc.displayName))
        else
            Logger:log("ERROR", string.format("Animation not found: %s", emoteName))
        end
    end
end

function NPCManagerV3:moveNPC(npc, targetPosition)
    Logger:log("MOVEMENT", string.format("Moving %s to position %s", 
        npc.displayName, 
        tostring(targetPosition)
    ))
    
    local Humanoid = npc.model:FindFirstChildOfClass("Humanoid")
    if Humanoid then
        Humanoid:MoveTo(targetPosition)
    else
        Logger:log("ERROR", string.format("Cannot move %s (no Humanoid)", npc.displayName))
    end
end

function NPCManagerV3:stopFollowing(npc)
    npc.isFollowing = false
    npc.followTarget = nil
    npc.followStartTime = nil

    -- Stop movement and animations
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        humanoid:MoveTo(npc.model.PrimaryPart.Position)
        AnimationManager:stopAnimations(humanoid)
    end

    Logger:log("MOVEMENT", string.format("%s stopped following and movement halted", npc.displayName))
end

function NPCManagerV3:updateNPCState(npc)
    if not npc.model or not npc.model.PrimaryPart then return end
    
    self:updateNPCVision(npc)
    
    -- Only check for NPC interactions if not already interacting
    if not npc.isInteracting then
        self:checkNPCInteractions(npc)
    end
    
    local humanoid = npc.model:FindFirstChild("Humanoid")

    if npc.isFollowing then
        self:updateFollowing(npc)
        if humanoid then
            AnimationManager:playAnimation(humanoid, "walk")
        end
    elseif npc.isInteracting then
        if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
            Logger:log("INTERACTION", string.format("%s moved out of range, ending interaction", npc.interactingPlayer.Name))
            self:endInteraction(npc, npc.interactingPlayer)
        end
    elseif not npc.isMoving then
        -- Trigger idle animation if the NPC is not moving or following
        if humanoid then
            AnimationManager:playAnimation(humanoid, "idle")
        end
        self:randomWalk(npc)
    end
end

function NPCManagerV3:isPlayerInRange(npc, player)
    local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local npcPosition = npc.model and npc.model.PrimaryPart

    if playerPosition and npcPosition then
        local distance = (playerPosition.Position - npcPosition.Position).Magnitude
        local inRange = distance <= npc.responseRadius
        Logger:log("VISION", string.format("Distance check for %s to %s: %.2f units (in range: %s)", 
            npc.displayName, 
            player.Name, 
            distance, 
            tostring(inRange)
        ))
        return inRange
    end
    return false
end

function NPCManagerV3:updateFollowing(npc)
    if not npc.isFollowing then
        return -- Exit early if not following
    end
    if not npc.followTarget or not npc.followTarget.Character then
        Logger:log("MOVEMENT", string.format("%s: Follow target lost, stopping follow", npc.displayName))
        self:stopFollowing(npc)
        return
    end

    local targetPosition = npc.followTarget.Character:FindFirstChild("HumanoidRootPart")
    if not targetPosition then
        Logger:log("MOVEMENT", string.format("%s: Cannot find target position, stopping follow", npc.displayName))
        self:stopFollowing(npc)
        return
    end

    local npcPosition = npc.model.PrimaryPart.Position
    local direction = (targetPosition.Position - npcPosition).Unit
    local distance = (targetPosition.Position - npcPosition).Magnitude

    if distance > MIN_FOLLOW_DISTANCE + 1 then
        local newPosition = npcPosition + direction * (distance - MIN_FOLLOW_DISTANCE)
        Logger:log("MOVEMENT", string.format("%s moving to %s", npc.displayName, tostring(newPosition)))
        npc.model.Humanoid:MoveTo(newPosition)
    else
        Logger:log("MOVEMENT", string.format("%s is close enough to target", npc.displayName))
        npc.model.Humanoid:Move(Vector3.new(0, 0, 0)) -- Stop moving
    end

    -- Check if follow duration has expired
    if tick() - npc.followStartTime > FOLLOW_DURATION then
        Logger:log("MOVEMENT", string.format("%s: Follow duration expired, stopping follow", npc.displayName))
        self:stopFollowing(npc)
    end
end

function NPCManagerV3:randomWalk(npc)
    if npc.isInteracting or npc.isMoving then
        Logger:log("MOVEMENT", string.format("%s cannot perform random walk (interacting or moving)", npc.displayName))
        return
    end

    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        local currentPosition = npc.model.PrimaryPart.Position
        local randomOffset = Vector3.new(math.random(-5, 5), 0, math.random(-5, 5))
        local targetPosition = currentPosition + randomOffset

        npc.isMoving = true
        Logger:log("MOVEMENT", string.format("%s starting random walk to %s", 
            npc.displayName, 
            tostring(targetPosition)
        ))

        -- Play walk animation
        AnimationManager:playAnimation(humanoid, "walk")

        humanoid:MoveTo(targetPosition)
        humanoid.MoveToFinished:Connect(function(reached)
            npc.isMoving = false
            if reached then
                Logger:log("MOVEMENT", string.format("%s reached destination", npc.displayName))
            else
                Logger:log("MOVEMENT", string.format("%s failed to reach destination", npc.displayName))
            end

            -- Stop walk animation after reaching
            AnimationManager:stopAnimations(humanoid)
        end)
    else
        Logger:log("ERROR", string.format("%s cannot perform random walk (no Humanoid)", npc.displayName))
    end
end

function NPCManagerV3:getPerceptionData(npc)
	local visibleObjects = {}
	local visiblePlayers = {}
	
	for _, entity in ipairs(npc.visibleEntities) do
		if entity.type == "object" then
			table.insert(visibleObjects, entity.name .. " (" .. entity.objectType .. ")")
		elseif entity.type == "player" then
			table.insert(visiblePlayers, entity.name)
		end
	end

	Logger:log("VISION", string.format("%s perception update: %d objects, %d players", 
		npc.displayName,
		#visibleObjects,
		#visiblePlayers
	))

	return {
		visible_objects = visibleObjects,
		visible_players = visiblePlayers,
		memory = self:getRecentMemories(npc),
	}
end

function NPCManagerV3:getPlayerContext(player)
	local context = {
		player_name = player.Name,
		is_new_conversation = self:isNewConversation(player),
		time_since_last_interaction = self:getTimeSinceLastInteraction(player),
		nearby_players = self:getNearbyPlayerNames(player),
		npc_location = self:getNPCLocation(player),
	}

	Logger:log("STATE", string.format("Context generated for %s: %s", 
		player.Name,
		HttpService:JSONEncode(context)
	))

	return context
end

function NPCManagerV3:getVisibleObjects(npc)
	-- Implementation depends on your game's object system
	return {}
end

function NPCManagerV3:getVisiblePlayers(npc)
	local visiblePlayers = {}
	for _, player in ipairs(Players:GetPlayers()) do
		if self:isPlayerInRange(npc, player) then
			table.insert(visiblePlayers, player.Name)
		end
	end
	return visiblePlayers
end

function NPCManagerV3:getRecentMemories(npc)
	-- Implementation depends on how you store memories
	return {}
end

function NPCManagerV3:isNewConversation(player)
	-- Implementation depends on how you track conversations
	return true
end

function NPCManagerV3:getTimeSinceLastInteraction(player)
	-- Implementation depends on how you track interactions
	return "N/A"
end

function NPCManagerV3:getNearbyPlayerNames(player)
	-- Implementation depends on your game's proximity system
	return {}
end

function NPCManagerV3:getNPCLocation(player)
	-- Implementation depends on how you represent locations in your game
	return "Unknown"
end

function NPCManagerV3:testFollowFunctionality(npcId, playerId)
    local npc = self.npcs[npcId]
    local player = Players:GetPlayerByUserId(playerId)
    
    if npc and player then
        Logger:log("DEBUG", string.format("Testing follow functionality for NPC: %s", npc.displayName))
        self:startFollowing(npc, player)
        wait(5) -- Wait for 5 seconds
        self:updateFollowing(npc)
        wait(5) -- Wait another 5 seconds
        self:stopFollowing(npc)
        Logger:log("DEBUG", string.format("Follow test completed for NPC: %s", npc.displayName))
    else
        Logger:log("ERROR", "Failed to find NPC or player for follow test")
    end
end

function NPCManagerV3:testFollowCommand(npcId, playerId)
	local npc = self.npcs[npcId]
	local player = game.Players:GetPlayerByUserId(playerId)
	if npc and player then
		Logger:log("MOVEMENT", string.format("Testing follow command for %s", npc.displayName))
		self:startFollowing(npc, player)
	else
		Logger:log("ERROR", "Failed to find NPC or player for follow test")
	end
end

function NPCManagerV3:getInteractionClusters(player)
    local clusters = {}
    local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    
    if not playerPosition then
        Logger:log("ERROR", string.format("Cannot get interaction clusters for %s (no character/HumanoidRootPart)", player.Name))
        return clusters
    end

    for _, npc in pairs(self.npcs) do
        local distance = (npc.model.PrimaryPart.Position - playerPosition.Position).Magnitude
        if distance <= npc.responseRadius then
            local addedToCluster = false
            for _, cluster in ipairs(clusters) do
                if (cluster.center - npc.model.PrimaryPart.Position).Magnitude < 10 then
                    table.insert(cluster.npcs, npc)
                    addedToCluster = true
                    Logger:log("INTERACTION", string.format("Added %s to existing cluster", npc.displayName))
                    break
                end
            end
            if not addedToCluster then
                Logger:log("INTERACTION", string.format("Created new cluster for %s", npc.displayName))
                table.insert(clusters, { center = npc.model.PrimaryPart.Position, npcs = { npc } })
            end
        end
    end

    Logger:log("INTERACTION", string.format("Found %d interaction clusters for %s", #clusters, player.Name))
    return clusters
end

-- Update createMockParticipant to include necessary references
function NPCManagerV3:createMockParticipant(npc)
    local MockPlayer = require(game.ServerScriptService.MockPlayer)
    local mockId = tonumber(npc.id) or 0
    local participant = MockPlayer.new(npc.displayName, mockId, "npc")
    
    participant.displayName = npc.displayName
    participant.UserId = mockId
    participant.npcId = npc.id
    participant.model = npc.model
    
    participant.IsA = function(self, className)
        return className == "Player" and false or true
    end
    
    return participant
end

-- Add back initiateNPCInteraction
function NPCManagerV3:initiateNPCInteraction(npc1, npc2)
    if npc1.isInteracting or npc2.isInteracting then
        Logger:log("INTERACTION", "Cannot initiate interaction: one of the NPCs is busy")
        return
    end

    local npc1Participant = self:createMockParticipant(npc1)
    self:handleNPCInteraction(npc2, npc1Participant, "Hello, " .. npc2.displayName .. "!")
end

-- Add new helper functions for NPC state management
function NPCManagerV3:lockNPCInPlace(npc)
    if not npc or not npc.model then return end
    
    npc.isMoving = false
    npc.previousWalkSpeed = npc.model.Humanoid.WalkSpeed -- Store original speed
    npc.model.Humanoid.WalkSpeed = 0
    
    Logger:log("MOVEMENT", string.format("Locked NPC %s in place", npc.displayName))
end

function NPCManagerV3:unlockNPC(npc)
    if not npc or not npc.model then return end
    
    npc.isMoving = true
    if npc.previousWalkSpeed then
        npc.model.Humanoid.WalkSpeed = npc.previousWalkSpeed
    end
    
    Logger:log("MOVEMENT", string.format("Unlocked NPC %s", npc.displayName))
end

-- Add NPC-to-NPC interaction trigger check
function NPCManagerV3:checkNPCInteractions(npc)
    if npc.isInteracting then return end -- Skip if already in interaction

    -- Get current time for cooldown check
    local currentTime = tick()
    if (currentTime - (npc.lastInteractionTime or 0)) < 30 then
        return -- Still in cooldown
    end

    for _, entity in ipairs(npc.visibleEntities) do
        if entity.type == "npc" then
            local otherNPC = entity.instance
            -- Only interact if both NPCs are free and within range
            if not otherNPC.isInteracting 
               and entity.distance < npc.responseRadius 
               and math.random() < 0.02 then -- 2% chance
                
                Logger:log("INTERACTION", string.format("NPC %s initiating conversation with %s",
                    npc.displayName,
                    otherNPC.displayName
                ))
                npc.lastInteractionTime = currentTime
                self:initiateNPCInteraction(npc, otherNPC)
                break
            end
        end
    end
end

-- Add back getResponseFromAI function
function NPCManagerV3:getResponseFromAI(npc, participant, message)
    local interactionState = self.interactionController:getInteractionState(participant)
    local participantMemory = npc.shortTermMemory[participant.UserId] or {}

    local cacheKey = self:getCacheKey(npc, participant, message)
    if self.responseCache[cacheKey] then
        return self.responseCache[cacheKey]
    end

    local data = {
        message = message,
        player_id = tostring(participant.UserId),
        npc_id = npc.id,
        npc_name = npc.displayName,
        system_prompt = npc.system_prompt,
        perception = self:getPerceptionData(npc),
        context = self:getPlayerContext(participant),
        interaction_state = interactionState,
        memory = participantMemory,
        limit = 200,
    }

    local success, response = pcall(function()
        return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
    end)

    if success then
        Logger:log("API", string.format("Raw API response: %s", response))
        local parsed = HttpService:JSONDecode(response)
        if parsed and parsed.message then
            self.responseCache[cacheKey] = parsed
            npc.shortTermMemory[participant.UserId] = {
                lastInteractionTime = tick(),
                recentTopics = parsed.topics_discussed or {},
            }
            return parsed
        else
            Logger:log("ERROR", "Invalid response format received from API")
        end
    else
        Logger:log("ERROR", string.format("Failed to get AI response: %s", tostring(response)))
    end

    return nil
end

-- Add back processAIResponse function
function NPCManagerV3:processAIResponse(npc, participant, response)
    Logger:log("RESPONSE", string.format("Processing AI response for %s: %s",
        npc.displayName,
        HttpService:JSONEncode(response)
    ))

    if response.message then
        Logger:log("CHAT", string.format("Displaying message from %s: %s",
            npc.displayName,
            response.message
        ))
        self:displayMessage(npc, response.message, participant)
    end

    if response.action then
        Logger:log("ACTION", string.format("Executing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.action)
        ))
        self:executeAction(npc, participant, response.action)
    end

    if response.internal_state then
        Logger:log("STATE", string.format("Updating internal state for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.internal_state)
        ))
        self:updateInternalState(npc, response.internal_state)
    end
end

return NPCManagerV3
