-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local ChatService = game:GetService("Chat")
local RunService = game:GetService("RunService")

-- Wait for critical paths and store references
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local services = NPCSystem:WaitForChild("services")
local chat = NPCSystem:WaitForChild("chat")
local config = NPCSystem:WaitForChild("config")

-- Update requires to use correct paths
local AnimationManager = require(Shared.AnimationManager)
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local NPCChatHandler = require(chat:WaitForChild("NPCChatHandler"))
local InteractionService = require(services:WaitForChild("InteractionService"))
local LoggerService = require(services:WaitForChild("LoggerService"))

LoggerService:info("SYSTEM", "Attempting to load services...")
local success, result = pcall(function()
    local vision = require(services:WaitForChild("VisionService"))
    local movement = require(services:WaitForChild("MovementService"))
    LoggerService:info("SYSTEM", "Services loaded successfully")
    return {vision = vision, movement = movement}
end)

if not success then
    warn("Failed to load services:", result)
end

local VisionService = result.vision
local MovementService = result.movement

-- Initialize Logger
local Logger
local function initializeLogger()
    local success, result = pcall(function()
        if game:GetService("RunService"):IsServer() then
            return require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
        else
            return require(ReplicatedStorage.Shared.NPCSystem.services.LoggerService)
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
LoggerService:info("SYSTEM", "NPCManagerV3 module loaded")

local NPCManagerV3 = {}
NPCManagerV3.__index = NPCManagerV3

-- Add singleton instance variable
local instance = nil

-- Add near the top with other local variables
local ThreadManager = {
    activeThreads = {},
    maxThreads = 10
}

-- Add this new function for thread management
function NPCManagerV3:initializeThreadManager()
    -- Initialize thread pool
    self.threadPool = {
        interactionThreads = {},
        movementThreads = {},
        visionThreads = {}
    }
    
    -- Thread limits
    self.threadLimits = {
        interaction = 5,
        movement = 3,
        vision = 2
    }
    
    LoggerService:debug("SYSTEM", "Thread manager initialized")
end

function NPCManagerV3.getInstance()
    if not instance then
        instance = setmetatable({}, NPCManagerV3)
        
        LoggerService:info("SYSTEM", "Initializing NPCManagerV3...")
        
        -- Initialize core components first
        instance.npcs = {}
        instance.responseCache = {}
        instance.activeInteractions = {}
        instance.movementStates = {}
        instance.activeConversations = {}
        instance.lastInteractionTime = {}
        instance.conversationCooldowns = {}
        
        -- Initialize thread manager
        instance:initializeThreadManager()
        
        -- Initialize services
        instance.movementService = MovementService.new()
        instance.interactionController = require(game.ServerScriptService.InteractionController).new()
        
        LoggerService:info("SYSTEM", "Services initialized")
        
        -- Load NPC database
        instance:loadNPCDatabase()
        
        LoggerService:info("SYSTEM", "NPCManagerV3 initialization complete")
    end
    return instance
end

-- Replace .new() with modified version
function NPCManagerV3.new()
    local manager = NPCManagerV3.getInstance()
    -- Ensure database is loaded
    if not manager.databaseLoaded then
        manager:loadNPCDatabase()
        manager.databaseLoaded = true
    end
    return manager
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

-- Add handler for player messages at initialization
NPCChatEvent.OnServerEvent:Connect(function(player, data)
    NPCManagerV3:getInstance():handlePlayerMessage(player, data)
end)

function NPCManagerV3:handlePlayerMessage(player, data)
    local npcName = data.npcName
    local message = data.message
    
    LoggerService:debug("CHAT", string.format("Received message from player %s to NPC %s: %s",
        player.Name,
        npcName,
        message
    ))
    
    -- Find the NPC by name
    for _, npc in pairs(self.npcs) do
        if npc.displayName == npcName then
            -- Check if the NPC is interacting with this player
            if npc.isInteracting and npc.interactingPlayer == player then
                -- Handle the interaction
                self:handleNPCInteraction(npc, player, message)
            else
                LoggerService:debug("INTERACTION", string.format("NPC %s is not interacting with player %s", 
                    npc.displayName, 
                    player.Name
                ))
            end
            return
        end
    end
    
    LoggerService:error("ERROR", string.format("NPC %s not found when handling player message", npcName))
end

function NPCManagerV3:loadNPCDatabase()
    if self.databaseLoaded then
        LoggerService:debug("DATABASE", "Database already loaded, skipping...")
        return
    end
    
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    LoggerService:debug("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
    for _, npcData in ipairs(npcDatabase.npcs) do
        self:createNPC(npcData)
    end
    
    self.databaseLoaded = true
    LoggerService:debug("DATABASE", "NPC Database loaded successfully")
end

function NPCManagerV3:createNPC(npcData)
    LoggerService:debug("NPC", string.format("Creating NPC: %s", npcData.displayName))
    
    -- Debug log NPC data
    LoggerService:debug("DEBUG", string.format("Creating NPC with data: %s", 
        HttpService:JSONEncode({
            displayName = npcData.displayName,
            abilities = npcData.abilities
        })
    ))

    -- Ensure NPCs folder exists
    if not workspace:FindFirstChild("NPCs") then
        Instance.new("Folder", workspace).Name = "NPCs"
        LoggerService:debug("SYSTEM", "Created NPCs folder in workspace")
    end

    -- Create and set up NPC model
    local model = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
    if not model then
        LoggerService:error("NPC", string.format("Model not found for NPC: %s", npcData.displayName))
        return
    end

    local npcModel = model:Clone()
    npcModel.Name = npcData.displayName
    npcModel.Parent = workspace.NPCs

    -- Validate required parts
    local humanoidRootPart = npcModel:FindFirstChild("HumanoidRootPart")
    local humanoid = npcModel:FindFirstChildOfClass("Humanoid")
    local head = npcModel:FindFirstChild("Head")

    if not humanoidRootPart or not humanoid or not head then
        LoggerService:error("NPC", string.format("NPC model %s is missing essential parts", npcData.displayName))
        npcModel:Destroy()
        return
    end

    -- Set up NPC instance
    local npc = {
        model = npcModel,
        id = npcData.id,
        displayName = npcData.displayName,
        responseRadius = npcData.responseRadius,
        system_prompt = npcData.system_prompt,
        abilities = npcData.abilities or {},
        playersInRange = {},
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

    -- Initialize components
    npcModel.PrimaryPart = humanoidRootPart
    humanoidRootPart.CFrame = CFrame.new(npcData.spawnPosition)
    AnimationManager:applyAnimations(humanoid)
    self:initializeNPCChatSpeaker(npc)
    self:setupClickDetector(npc)

    -- Store NPC reference
    self.npcs[npc.id] = npc
    
    LoggerService:debug("NPC", string.format("NPC added: %s (Total NPCs: %d)", npc.displayName, self:getNPCCount()))
    
    return npc
end

-- Add a separate function to test chat for all NPCs
function NPCManagerV3:testAllNPCChat()
    LoggerService:debug("TEST", "Testing chat for all NPCs...")
    for _, npc in pairs(self.npcs) do
        if npc.model and npc.model:FindFirstChild("Head") then
            -- Try simple chat method only
            game:GetService("Chat"):Chat(npc.model.Head, "Test chat from " .. npc.displayName)
            wait(0.5) -- Small delay between tests
        end
    end
    LoggerService:debug("TEST", "Chat testing complete")
end

function NPCManagerV3:getNPCCount()
	local count = 0
	for _ in pairs(self.npcs) do
		count = count + 1
	end
	LoggerService:debug("DEBUG", string.format("Current NPC count: %d", count))
	return count
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius

	-- Try to parent to HumanoidRootPart, if not available, use any BasePart
	local parent = npc.model:FindFirstChild("HumanoidRootPart") or npc.model:FindFirstChildWhichIsA("BasePart")

	if parent then
		clickDetector.Parent = parent
		LoggerService:debug("INTERACTION", string.format("Set up ClickDetector for %s with radius %d", 
			npc.displayName, 
			npc.responseRadius
		))
	else
		LoggerService:error("ERROR", string.format("Could not find suitable part for ClickDetector on %s", npc.displayName))
		return
	end

	clickDetector.MouseClick:Connect(function(player)
		-- Send system message about player clicking
		local systemMessage = string.format(
			"[SYSTEM] %s has clicked to interact with you. You can start a conversation.",
			player.Name
		)
		self:handleNPCInteraction(npc, player, systemMessage)
	end)
end

function NPCManagerV3:startInteraction(npc1, npc2)
    if not InteractionService:canInteract(npc1, npc2) then
        return false
    end
    
    InteractionService:lockNPCsForInteraction(npc1, npc2)
    
    -- Old interaction code...
end

function NPCManagerV3:endInteraction(npc1, npc2)
    InteractionService:unlockNPCsAfterInteraction(npc1, npc2)
    
    -- Rest of cleanup code...
end

function NPCManagerV3:getCacheKey(npc, player, message)
	local context = {
		npcId = npc.id,
		
		playerId = player.UserId,
		message = message,
		memory = npc.shortTermMemory[player.UserId],
	}
	
	local key = HttpService:JSONEncode(context)
	LoggerService:debug("DEBUG", string.format("Generated cache key for %s and %s", npc.displayName, player.Name))
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

function NPCManagerV3:updateNPCVision()
    -- Early return if vision is disabled in config
    if not PerformanceConfig.NPC.VisionEnabled then return end

    for _, npc in pairs(self.activeNPCs) do
        -- Process in batches to spread load
        if self.visionUpdateCount and self.visionUpdateCount % PerformanceConfig.NPC.RaycastBatchSize == 0 then
            RunService.Heartbeat:Wait()
        end
        self.visionUpdateCount = (self.visionUpdateCount or 0) + 1

        local model = npc.model
        if not model then continue end

        local head = model:FindFirstChild("Head")
        if not head then continue end

        -- Get nearby players
        for _, player in pairs(game.Players:GetPlayers()) do
            local character = player.Character
            if not character then continue end

            local targetHead = character:FindFirstChild("Head")
            if not targetHead then continue end

            local toTarget = (targetHead.Position - head.Position)
            -- Check max vision distance from config
            if toTarget.Magnitude > PerformanceConfig.NPC.MaxVisionDistance then
                continue
            end

            -- Check vision cone angle from config
            local forward = model.PrimaryPart.CFrame.LookVector
            local angle = math.deg(math.acos(forward:Dot(toTarget.Unit)))
            if angle > PerformanceConfig.NPC.VisionConeAngle/2 then
                continue
            end

            -- Skip raycast if occlusion checks disabled
            if PerformanceConfig.NPC.SkipOccludedTargets then
                local params = RaycastParams.new()
                params.FilterType = Enum.RaycastFilterType.Blacklist
                params.FilterDescendantsInstances = {model}

                local result = workspace:Raycast(head.Position, toTarget, params)
                if result and result.Instance:IsDescendantOf(character) then
                    -- Handle NPC seeing player...
                    self:handleNPCVision(npc, player)
                end
            else
                -- No occlusion check, just handle vision
                self:handleNPCVision(npc, player)
            end
        end
    end

    -- Wait configured update interval before next vision update
    wait(PerformanceConfig.NPC.VisionUpdateRate)
end

-- Update helper function to check if participant is NPC
-- Replace the isNPCParticipant function with this improved version
function NPCManagerV3:isNPCParticipant(participant)
    -- Check if it's a Player instance first
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        return false
    end
    
    -- Then check for NPC properties
    return participant.Type == "npc" or participant.npcId ~= nil
end

function NPCManagerV3:displayMessage(npc, message, recipient)
    -- Don't propagate error messages between NPCs
    if self:isNPCParticipant(recipient) and message == "I'm having trouble understanding right now." then
        LoggerService:log("CHAT", "Blocking error message propagation between NPCs")
        return
    end

    -- Ensure we have a valid model and head
    if not npc.model or not npc.model:FindFirstChild("Head") then
        LoggerService:error("ERROR", string.format("Cannot display message for %s - missing model or head", npc.displayName))
        return
    end

    -- Create chat bubble
    local success, err = pcall(function()
        game:GetService("Chat"):Chat(npc.model.Head, message)
        LoggerService:debug("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
    end)
    if not success then
        LoggerService:error("ERROR", string.format("Failed to create chat bubble: %s", err))
    end

    -- Handle NPC-to-NPC messages
    if self:isNPCParticipant(recipient) then
        LoggerService:debug("CHAT", string.format("NPC %s to NPC %s: %s",
            npc.displayName,
            recipient.displayName or recipient.Name,
            message
        ))
        
        -- Fire event to all clients for redundancy
        NPCChatEvent:FireAllClients({
            npcName = npc.displayName,
            message = message,
            type = "npc_chat"
        })

        -- Handle recipient response after a small delay
        if recipient.npcId then
            local recipientNPC = self.npcs[recipient.npcId]
            if recipientNPC then
                task.delay(1, function()
                    self:handleNPCInteraction(recipientNPC, self:createMockParticipant(npc), message)
                end)
            end
        end
        return
    end

    -- Handle player messages
    if typeof(recipient) == "Instance" and recipient:IsA("Player") then
        LoggerService:debug("CHAT", string.format("NPC %s sending message to player %s: %s",
            npc.displayName,
            recipient.Name,
            message
        ))
        
        -- Send to player's chat window
        NPCChatEvent:FireClient(recipient, {
            npcName = npc.displayName,
            message = message,
            type = "chat"
        })
        return
    end
end

-- And modify processAIResponse to directly use displayMessage
function NPCManagerV3:processAIResponse(npc, participant, response)
    if response.metadata and response.metadata.should_end then
        -- Set cooldown
        local cooldownKey = npc.id .. "_" .. participant.UserId
        self.conversationCooldowns[cooldownKey] = os.time()
        
        -- Unlock movement
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
            npc.isMovementLocked = false
        end
    end

    if response.message then
        self:displayMessage(npc, response.message, participant)
    end

    if response.action then
        LoggerService:debug("ACTION", string.format("Executing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.action)
        ))
        self:executeAction(npc, participant, response.action)
    end

    if response.internal_state then
        LoggerService:debug("STATE", string.format("Updating internal state for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.internal_state)
        ))
        self:updateInternalState(npc, response.internal_state)
    end
end


-- Add this new function to help manage NPC chat speakers
function NPCManagerV3:initializeNPCChatSpeaker(npc)
    if npc and npc.model then
        local createSpeaker = _G.CreateNPCSpeaker
        if createSpeaker then
            createSpeaker(npc.model)
            LoggerService:debug("SYSTEM", string.format("Initialized chat speaker for NPC: %s", npc.displayName))
        end
    end
end

-- Update the displayNPCToNPCMessage function in NPCManagerV3.lua
function NPCManagerV3:testChatBubbles(fromNPC)
    if not fromNPC or not fromNPC.model then
        LoggerService:error("ERROR", "Invalid NPC for chat test")
        return
    end

    local head = fromNPC.model:FindFirstChild("Head")
    if not head then
        LoggerService:error("ERROR", string.format("NPC %s has no Head part!", fromNPC.displayName))
        return
    end

    -- Try each chat method
    LoggerService:debug("TEST", "Testing chat methods...")

    -- Method 1: Direct Chat
    game:GetService("Chat"):Chat(head, "Test 1: Direct Chat")
    wait(2)

    -- Method 2: Legacy Chat
    head.Chatted:Fire("Test 2: Legacy Chat")
    wait(2)

    -- Method 3: BubbleChat
    local Chat = game:GetService("Chat")
    Chat:Chat(head, "Test 3: BubbleChat", Enum.ChatColor.Blue)
    wait(2)

    -- Method 4: ChatService
    local success, err = pcall(function()
        Chat:CreateTalkDialog(head)
        head:SetTextBubble("Test 4: ChatService")
    end)
    
    if not success then
        LoggerService:error("ERROR", "ChatService method failed: " .. tostring(err))
    end

    LoggerService:debug("TEST", "Chat test complete")
end

-- Also update displayNPCToNPCMessage to try all methods
function NPCManagerV3:displayNPCToNPCMessage(fromNPC, toNPC, message)
    if not (fromNPC and toNPC and message) then
        LoggerService:error("ERROR", "Missing required parameters for NPC-to-NPC message")
        return
    end

    LoggerService:debug("CHAT", string.format("NPC %s to NPC %s: %s", 
        fromNPC.displayName or "Unknown",
        toNPC.displayName or "Unknown",
        message
    ))
    
    -- Use the same direct Chat call that worked in our test
    if fromNPC.model and fromNPC.model:FindFirstChild("Head") then
        game:GetService("Chat"):Chat(fromNPC.model.Head, message)
        LoggerService:debug("CHAT", string.format("Created chat bubble for NPC: %s", fromNPC.displayName))
    end
    
    -- Fire event to all clients for redundancy
    NPCChatEvent:FireAllClients({
        npcName = fromNPC.displayName,
        message = message,
        type = "npc_chat"
    })
end

function NPCManagerV3:executeAction(npc, player, action)
    LoggerService:debug("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    if action.type == "stop_talking" then
        -- Stop following if we were following this player
        if npc.isFollowing and npc.followTarget == player then
            LoggerService:debug("MOVEMENT", string.format("Stopping follow as part of ending interaction: %s", player.Name))
            self:stopFollowing(npc)
        end
        -- Let the normal conversation flow handle the ending
    elseif action.type == "follow" then
        LoggerService:debug("MOVEMENT", string.format("Starting to follow player: %s", player.Name))
        self:startFollowing(npc, player)
    elseif action.type == "unfollow" then
        LoggerService:debug("MOVEMENT", string.format("Stopping following player: %s", player.Name))
        self:stopFollowing(npc)
    elseif action.type == "emote" and action.data and action.data.emote then
        LoggerService:debug("ANIMATION", string.format("Playing emote: %s", action.data.emote))
        self:playEmote(npc, action.data.emote)
    elseif action.type == "move" and action.data and action.data.position then
        LoggerService:debug("MOVEMENT", string.format("Moving to position: %s", 
            tostring(action.data.position)
        ))
        self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
    elseif action.type == "none" then
        LoggerService:debug("ACTION", "No action required")
    else
        LoggerService:error("ERROR", string.format("Unknown action type: %s", action.type))
    end
end

function NPCManagerV3:startFollowing(npc, player)
    LoggerService:debug("MOVEMENT", string.format(
        "Starting follow - NPC: %s, Player: %s",
        npc.displayName,
        player and player.Name or "nil"
    ))

    if not player then
        LoggerService:warn("MOVEMENT", "Cannot start following - no player provided")
        return false
    end

    if not player.Character then
        LoggerService:warn("MOVEMENT", string.format(
            "Cannot start following - no character for player %s",
            player.Name
        ))
        return false
    end

    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()
    npc.isWalking = false
    
    -- Pass the player's character as the target
    self:setNPCMovementState(npc, "following", {
        target = player.Character,
        targetId = player.UserId
    })

    -- Explicitly start following behavior
    if self.movementService then
        self.movementService:startFollowing(npc, player.Character, {
            distance = 5,
            updateRate = 0.1
        })
    else
        LoggerService:warn("MOVEMENT", "MovementService not initialized")
        return false
    end

    LoggerService:debug("MOVEMENT", string.format(
        "Follow state set for %s -> %s",
        npc.displayName,
        player.Name
    ))

    return true
end

function NPCManagerV3:updateInternalState(npc, internalState)
	LoggerService:debug("STATE", string.format("Updating internal state for %s: %s",
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
            LoggerService:debug("ANIMATION", string.format("Playing emote %s for %s", emoteName, npc.displayName))
        else
            LoggerService:error("ERROR", string.format("Animation not found: %s", emoteName))
        end
    end
end

function NPCManagerV3:moveNPC(npc, targetPosition)
    LoggerService:debug("MOVEMENT", string.format("Moving %s to position %s", 
        npc.displayName, 
        tostring(targetPosition)
    ))
    
    local Humanoid = npc.model:FindFirstChildOfClass("Humanoid")
    if Humanoid then
        Humanoid:MoveTo(targetPosition)
    else
        LoggerService:error("ERROR", string.format("Cannot move %s (no Humanoid)", npc.displayName))
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

    LoggerService:debug("MOVEMENT", string.format("%s stopped following and movement halted", npc.displayName))
end

function NPCManagerV3:handleNPCInteraction(npc, participant, message)
    -- Determine participant type
    local participantType = typeof(participant) == "Instance" and participant:IsA("Player") and "player" or "npc"
    local participantId = participantType == "player" and participant.UserId or participant.npcId
    local participantName = participant.Name or participant.displayName

    -- Clean up any existing interactions
    if npc.isInteracting then
        self:endInteraction(npc)
    end
    if participantType == "npc" and participant.isInteracting then
        self:endInteraction(participant)
    end

    LoggerService:debug(
        "Starting interaction - NPC: %s, Participant: %s (%s), Message: %s",
        npc.displayName,
        participantName,
        participantType,
        message
    )

    -- Generate unique interaction ID
    local interactionId = HttpService:GenerateGUID()
    
    -- Check if we can create new interaction thread
    if #self.threadPool.interactionThreads >= self.threadLimits.interaction then
        LoggerService:debug("THREAD", "Maximum interaction threads reached, queuing interaction")
        return
    end
    
    -- Create new thread for interaction
    local thread = task.spawn(function()
        -- Add thread to pool
        table.insert(self.threadPool.interactionThreads, interactionId)
        
        -- Original interaction logic
        local cooldownKey = npc.id .. "_" .. participant.UserId
        local lastInteraction = self.conversationCooldowns[cooldownKey]
        
        if lastInteraction and (os.time() - lastInteraction) < 30 then
            LoggerService:debug(
                "Interaction between %s and %s is on cooldown",
                npc.displayName,
                participant.Name
            )
            return
        end

        -- Lock movement at start of interaction
        if npc.model and npc.model:FindFirstChild("Humanoid") then
            npc.model.Humanoid.WalkSpeed = 0
            npc.isMovementLocked = true
            LoggerService:debug("MOVEMENT", string.format("Locked movement for %s during interaction", npc.displayName))
        end

        -- Check for conversation ending phrases
        local endPhrases = {
            "gotta run",
            "goodbye",
            "see you later",
            "bye",
            "talk to you later"
        }
        
        for _, phrase in ipairs(endPhrases) do
            if string.lower(message):find(phrase) then
                -- Set cooldown
                self.conversationCooldowns[cooldownKey] = os.time()
                
                -- Send goodbye response
                self:displayMessage(npc, "Goodbye! Talk to you later!", participant)
                
                -- Unlock movement
                if npc.model and npc.model:FindFirstChild("Humanoid") then
                    npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
                    npc.isMovementLocked = false
                end
                
                return nil
            end
        end

        local response = NPCChatHandler:HandleChat({
            message = message,
            npc_id = npc.id,
            participant_id = participantType == "player" and participant.UserId or participant.npcId,
            context = {
                participant_type = participantType,
                participant_name = participant.Name,
                is_new_conversation = false,
                interaction_history = {},
                nearby_players = self:getVisiblePlayers(npc),
                npc_location = "Unknown"
            }
        })
        
        if not response then
            -- Unlock movement on failure
            if npc.model and npc.model:FindFirstChild("Humanoid") then
                npc.model.Humanoid.WalkSpeed = npc.defaultWalkSpeed or 16
                npc.isMovementLocked = false
                LoggerService:debug("MOVEMENT", string.format("Unlocked movement for %s after failed interaction", npc.displayName))
            end
            return nil
        end

        -- Process response (this handles chat bubbles and actions)
        self:processAIResponse(npc, participant, response)

        -- Clean up thread when done
        for i, threadId in ipairs(self.threadPool.interactionThreads) do
            if threadId == interactionId then
                table.remove(self.threadPool.interactionThreads, i)
                break
            end
        end
    end)
    
    -- Monitor thread
    task.spawn(function()
        local success, result = pcall(function()
            task.wait(30) -- Timeout after 30 seconds
            if thread then
                task.cancel(thread)
                LoggerService:debug(string.format("Terminated hung interaction thread %s", interactionId))
            end
        end)
        
        if not success then
            LoggerService:error(string.format("Thread monitoring failed: %s", result))
        end
    end)
end

function NPCManagerV3:canNPCsInteract(npc1, npc2)
    -- Check if either NPC is in conversation
    for userId, activeNPC in pairs(self.activeConversations) do
        if activeNPC == npc1 or activeNPC == npc2 then
            LoggerService:debug(string.format(
                "Blocking NPC interaction: %s or %s is busy",
                npc1.displayName,
                npc2.displayName
            ))
            return false
        end
    end
    return true
end

function NPCManagerV3:createMockParticipant(npc)
    return {
        Name = npc.displayName,
        displayName = npc.displayName,
        UserId = npc.id,
        npcId = npc.id,
        Type = "npc",
        GetParticipantType = function() return "npc" end,
        GetParticipantId = function() return npc.id end,
        model = npc.model
    }
end

function NPCManagerV3:getVisiblePlayers(npc)
    local visiblePlayers = {}
    local npcPosition = npc.model and npc.model.PrimaryPart and npc.model.PrimaryPart.Position
    
    if not npcPosition then
        return visiblePlayers
    end
    
    for _, player in ipairs(game:GetService("Players"):GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= 50 then  -- 50 studs visibility range
                table.insert(visiblePlayers, player.Name)
            end
        end
    end
    
    return visiblePlayers
end

function NPCManagerV3:setNPCMovementState(npc, state, data)
    if not npc then return end
    
    -- Update movement state
    self.movementStates[npc.id] = {
        state = state,
        data = data or {},
        timestamp = os.time()
    }
    
    -- Handle state-specific logic
    if state == "idle" then
        self:stopFollowing(npc)
    elseif state == "following" then
        npc.isFollowing = true
        npc.followTarget = data.target
        npc.followStartTime = os.time()
    end
    
    LoggerService:debug(
        "Set %s movement state to %s",
        npc.displayName,
        state
    )
end

function NPCManagerV3:getNPCMovementState(npc)
    return self.movementStates[npc.id]
end

-- Add thread cleanup function
function NPCManagerV3:cleanupThreads()
    for threadType, threads in pairs(self.threadPool) do
        for i = #threads, 1, -1 do
            local threadId = threads[i]
            if not ThreadManager.activeThreads[threadId] then
                table.remove(threads, i)
                LoggerService:debug("THREAD", string.format("Cleaned up inactive %s thread %s", threadType, threadId))
            end
        end
    end
end

-- Add periodic thread cleanup
task.spawn(function()
    while true do
        task.wait(60) -- Clean up every minute
        NPCManagerV3:getInstance():cleanupThreads()
    end
end)

function NPCManagerV3:updateNPCPosition(npc)
    if npc.movementState == "free" then
        local randomPos = MovementService:getRandomPosition(npc.spawnPosition, npc.wanderRadius)
        MovementService:moveNPCToPosition(npc, randomPos)
    end
end

return NPCManagerV3
