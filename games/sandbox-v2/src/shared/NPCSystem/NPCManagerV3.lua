-- NPCManagerV3.lua
-- Version: v3.1.0-clusters
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local ChatService = game:GetService("Chat")
local RunService = game:GetService("RunService")
local workspace = game:GetService("Workspace")

-- Wait for critical paths and store references
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local services = NPCSystem:WaitForChild("services")
local chat = NPCSystem:WaitForChild("chat")
local config = NPCSystem:WaitForChild("config")

-- Update requires to use correct paths
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local NPCChatHandler = require(chat:WaitForChild("NPCChatHandler"))
local InteractionService = require(services:WaitForChild("InteractionService"))
local LoggerService = require(services:WaitForChild("LoggerService"))
local ModelLoader = require(script.Parent.services.ModelLoader)
local AnimationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.AnimationService)
local GameStateService = require(script.Parent.services.GameStateService)
local NPCChatDisplay = require(script.Parent.chat.NPCChatDisplay)

ModelLoader.init()
LoggerService:info("SYSTEM", string.format("Using ModelLoader v%s", ModelLoader.Version))

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
NPCManagerV3.VERSION = "v3.1.0-clusters"  -- Add as property, not in initial table
NPCManagerV3.__index = NPCManagerV3

-- Keep the singleton instance
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
        
        LoggerService:info("SYSTEM", string.format("Initializing NPCManagerV3 %s...", NPCManagerV3.VERSION))
        
        -- Initialize core components first
        instance.npcs = {}
        instance.responseCache = {}
        instance.activeInteractions = {}
        instance.movementStates = {}
        instance.activeConversations = {}
        instance.lastInteractionTime = {}
        instance.conversationCooldowns = {}
        instance.initializationComplete = false  -- Add this flag
        
        -- Initialize thread manager
        instance:initializeThreadManager()
        
        -- Initialize services
        instance.movementService = MovementService.new()
        instance.interactionController = require(game.ServerScriptService.InteractionController).new()
        instance.interactionService = InteractionService.new(instance)
        
        -- Start update loop
        game:GetService("RunService").Heartbeat:Connect(function()
            instance:update()
        end)
        
        LoggerService:info("SYSTEM", "Services initialized")
        
        -- Load NPC database
        instance:loadNPCDatabase()
        
        -- Set initialization complete
        instance.initializationComplete = true  -- Set flag after initialization
        
        -- Initialize NPCChatHandler
        NPCChatHandler:init(instance)
        
        LoggerService:info("SYSTEM", string.format("NPCManagerV3 %s initialization complete", NPCManagerV3.VERSION))
    end
    return instance
end

-- Make new() use getInstance()
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

-- Add handler for player messages at initialization
NPCChatEvent.OnServerEvent:Connect(function(player, data)
    NPCManagerV3:getInstance():handlePlayerMessage(player, data)
end)

function NPCManagerV3:handlePlayerMessage(player, data)
    local message = data.message
    
    LoggerService:debug("CHAT", string.format("Received message from player %s: %s",
        player.Name,
        message
    ))
    
    -- Get current clusters
    local clusters = InteractionService:getLatestClusters()
    if not clusters then
        LoggerService:warn("CHAT", "No clusters available")
        return
    end
    
    -- Find player's cluster
    local playerCluster
    for _, cluster in ipairs(clusters) do
        for _, member in ipairs(cluster.members) do
            if member.UserId == player.UserId then
                playerCluster = cluster
                break
            end
        end
        if playerCluster then break end
    end
    
    if not playerCluster then
        LoggerService:debug("CHAT", "Player not in any cluster")
        return
    end
    
    -- Send message to all NPCs in the cluster
    for _, member in ipairs(playerCluster.members) do
        if member.Type == "npc" then
            local npc = self.npcs[member.id]
            if npc then
                LoggerService:debug("CHAT", string.format("Routing message to cluster member: %s", npc.displayName))
                self:handleNPCInteraction(npc, player, message)
            end
        end
    end
end

function NPCManagerV3:loadNPCDatabase()
    LoggerService:debug("DATABASE", "Loading NPCs from database...")
    
    -- Get database from Data folder
    local success, database = pcall(function()
        return require(ReplicatedStorage:WaitForChild("Data"):WaitForChild("NPCDatabase"))
    end)
    
    if not success then
        LoggerService:error("DATABASE", "Failed to load NPCDatabase: " .. tostring(database))
        return false
    end
    
    if not database or not database.npcs then
        LoggerService:error("DATABASE", "Invalid database format - missing npcs table")
        return false
    end
    
    LoggerService:debug("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #database.npcs))
    
    for _, npcData in ipairs(database.npcs) do
        if npcData and npcData.displayName then
            self:createNPC(npcData)
        else
            LoggerService:warn("DATABASE", "Skipping invalid NPC data entry")
        end
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

    -- Ensure NPCs folder exists in Workspace (can be created dynamically)
    local NPCsFolder = workspace:FindFirstChild("NPCs")
    if not NPCsFolder or not NPCsFolder:IsA("Folder") then
        NPCsFolder = Instance.new("Folder")
        NPCsFolder.Name = "NPCs"
        NPCsFolder.Parent = workspace
        print("Created 'NPCs' folder in workspace.")
    end

    -- Create and set up NPC model
    if not npcData or not npcData.displayName then
        LoggerService:error("NPC", "Invalid NPC data - missing displayName")
        return
    end
    
    if not npcData.model then
        LoggerService:error("NPC", string.format("Invalid NPC data for %s - missing model ID", npcData.displayName))
        return
    end
    
    LoggerService:debug("NPC", string.format("Loading model for %s with ID: %s", 
        tostring(npcData.displayName), 
        tostring(npcData.model)
    ))
    
    -- Check if Pete's model exists
    if npcData.displayName == "Pete" then
        LoggerService:info("NPC", "Attempting to load Pete's model...")
        LoggerService:info("NPC", "Checking ServerStorage structure:")
        for _, child in ipairs(ServerStorage:GetChildren()) do
            LoggerService:info("NPC", "  - " .. child.Name)
            if child.Name == "Assets" then
                LoggerService:info("NPC", "    Found Assets folder")
                for _, assetChild in ipairs(child:GetChildren()) do
                    LoggerService:info("NPC", "    - " .. assetChild.Name)
                    if assetChild.Name == "npcs" then
                        LoggerService:info("NPC", "      Found npcs folder")
                        for _, npcModel in ipairs(assetChild:GetChildren()) do
                            LoggerService:info("NPC", "      - " .. npcModel.Name)
                        end
                    end
                end
            end
        end

        local peteModel = ServerStorage.Assets.npcs:FindFirstChild(npcData.model)
        if peteModel then
            LoggerService:info("NPC", "Found Pete's model in local assets")
            LoggerService:info("NPC", string.format("Model details: Type=%s, Name=%s", peteModel.ClassName, peteModel.Name))
        else
            LoggerService:error("NPC", "Pete's model not found in local assets")
        end
    end
    
    local model = ModelLoader.loadModel(npcData.model)
    if not model then
        LoggerService:error("NPC", string.format("Model not found for NPC: %s", npcData.displayName))
        return
    end

    -- Log model details
    LoggerService:info("NPC", string.format("Loaded model for %s:", npcData.displayName))
    LoggerService:info("NPC", string.format("  - Type: %s", model.ClassName))
    LoggerService:info("NPC", string.format("  - Name: %s", model.Name))
    LoggerService:info("NPC", string.format("  - Children: %d", #model:GetChildren()))
    for _, child in ipairs(model:GetChildren()) do
        LoggerService:info("NPC", string.format("  - Child: %s (%s)", child.Name, child.ClassName))
    end

    local npcModel = model:Clone()
    
    -- Handle R15 model setup
    local function setupR15Model(model)
        local humanoid = model:FindFirstChild("Humanoid")
        if humanoid then
            humanoid.RigType = Enum.HumanoidRigType.R15
        end
        
        -- Ensure all MeshParts are visible
        for _, part in ipairs(model:GetDescendants()) do
            if part:IsA("MeshPart") then
                part.Transparency = 0
            end
        end
    end
    
    -- Ensure model is properly set up
    for _, child in ipairs(npcModel:GetChildren()) do
        if child:IsA("Accessory") then
            LoggerService:debug("NPC", string.format("Setting up accessory: %s", child.Name))
            -- Ensure accessory handle is visible
            local handle = child:FindFirstChild("Handle")
            if handle then
                handle.Transparency = 0
            end
            child.Parent = npcModel
        elseif child:IsA("Shirt") or child:IsA("Pants") or child:IsA("BodyColors") then
            LoggerService:debug("NPC", string.format("Setting up clothing: %s", child.Name))
            child.Parent = npcModel
        end
    end
    
    -- Set up R15 model if needed
    if npcModel:FindFirstChild("UpperTorso") then
        LoggerService:info("NPC", "Setting up R15 model")
        setupR15Model(npcModel)
    end
    
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
        responseRadius = npcData.responseRadius or 20,  -- Increase default radius
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
        currentLocation = npcData.location or "Unknown"
    }

    -- Initialize components
    npcModel.PrimaryPart = humanoidRootPart
    humanoidRootPart.CFrame = CFrame.new(npcData.spawnPosition)
    -- Temporarily disable animations
    AnimationService:applyAnimations(humanoid)
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
    -- Remove local gatekeeping, just pass through to backend
    LoggerService:debug("INTERACTION", string.format(
        "Forwarding interaction request to backend: %s <-> %s",
        npc1.displayName, npc2.displayName
    ))
    return true
end

function NPCManagerV3:endInteraction(npc, participant)
    -- Only handle cleanup of conversation state
    if npc.isInteracting then
        npc.isInteracting = false
        npc.interactingPlayer = nil
    end
    -- Remove any movement lock handling
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

function NPCManagerV3:processAIResponse(npc, participant, response)
    if response.message then
        LoggerService:debug("CHAT", string.format(
            "Attempting to display message from %s: %s",
            npc.displayName,
            response.message
        ))
        NPCChatDisplay:displayMessage(npc, response.message, participant)
    end

    if response.action and response.action.actions then
        for _, action in ipairs(response.action.actions) do
            if action.type ~= "none" then
                self:executeAction(npc, participant, action)
            end
        end
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

local USE_ACTION_SERVICE = true  -- Make sure this is true

function NPCManagerV3:executeAction(npc, player, action)
    LoggerService:debug("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    local ActionService = require(ReplicatedStorage.Shared.NPCSystem.services.ActionService)
    
    if action.type == "navigate" then
        LoggerService:debug("ACTION", string.format("Processing navigate action for %s", npc.displayName))
        local success = ActionService.navigate(npc, action)
        if not success then
            LoggerService:warn("ACTION", string.format(
                "Navigation failed for NPC %s",
                npc.displayName
            ))
        end
        
    elseif action.type == "follow" then
        if USE_ACTION_SERVICE then
            LoggerService:debug("ACTION", "Using ActionService to handle 'follow'")
            ActionService.follow(npc, player)
        else
            LoggerService:debug("ACTION", "Using LEGACY 'startFollowing' method for 'follow'")
            self:startFollowing(npc, player)
        end
        
    elseif action.type == "unfollow" then
        if USE_ACTION_SERVICE then
            LoggerService:debug("ACTION", "Using ActionService to handle 'unfollow'")
            ActionService.unfollow(npc)
        else
            LoggerService:debug("ACTION", "Using LEGACY 'stopFollowing' method for 'unfollow'")
            self:stopFollowing(npc)
        end
        
    elseif action.type == "emote" then
        LoggerService:debug("ACTION", "Using ActionService to handle 'emote'")
        local success = ActionService.emote(npc, action.data)
        if not success then
            LoggerService:warn("ACTION", string.format(
                "Emote failed for NPC %s",
                npc.displayName
            ))
        end
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
    AnimationService:playEmote(npc, emoteName)
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

    -- Tell MovementService to stop following
    if self.movementService then
        self.movementService:stopFollowing(npc)
    end

    -- Stop movement and animations
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        humanoid:MoveTo(npc.model.PrimaryPart.Position)
        AnimationManager:stopAnimations(humanoid)
    end

    -- Update movement state without recursion
    self.movementStates[npc.id] = {
        state = "idle",
        data = {},
        timestamp = os.time()
    }

    LoggerService:debug("MOVEMENT", string.format("%s stopped following and movement halted", npc.displayName))
end

-- Add at the top with other state variables
local recentMessages = {} -- Store recent message IDs to prevent duplicates
local MESSAGE_CACHE_TIME = 1 -- Time in seconds to cache messages

-- Add this helper function
local function generateMessageId(npcId, participantId, message)
    return string.format("%s_%s_%s", npcId, participantId, message)
end

-- Modify handleNPCInteraction to check for duplicates
function NPCManagerV3:handleNPCInteraction(npc, participant, message)
    -- Generate a unique ID for this message
    local messageId = generateMessageId(npc.id, participant.UserId, message)
    
    -- Check if this is a duplicate message
    if recentMessages[messageId] then
        if tick() - recentMessages[messageId] < MESSAGE_CACHE_TIME then
            return -- Skip duplicate message
        end
    end
    
    -- Store message timestamp
    recentMessages[messageId] = tick()
    
    -- Clean up old messages
    for id, timestamp in pairs(recentMessages) do
        if tick() - timestamp > MESSAGE_CACHE_TIME then
            recentMessages[id] = nil
        end
    end
    
    -- Determine participant type
    local participantType = typeof(participant) == "Instance" and participant:IsA("Player") and "player" or "npc"
    local participantId = participantType == "player" and participant.UserId or participant.npcId
    local participantName = participant.Name or participant.displayName

    LoggerService:debug(
        "Starting interaction - NPC: %s, Participant: %s (%s), Message: %s",
        npc.displayName,
        participantName,
        participantType,
        message
    )

    -- Generate unique interaction ID
    local interactionId = HttpService:GenerateGUID()
    
    -- Create new thread for interaction
    local thread = task.spawn(function()
        -- Add thread to pool
        table.insert(self.threadPool.interactionThreads, interactionId)
        
        local response = NPCChatHandler:HandleChat({
            message = message,
            npc_id = npc.id,
            participant_id = participantType == "player" and participant.UserId or participant.npcId,
            context = {
                participant_type = participantType,
                participant_name = participant.Name,
                speaker_name = npc.displayName, 
                is_new_conversation = true,
                interaction_history = {},
                nearby_players = self:getVisiblePlayers(npc),
                npc_location = "Unknown"
            }
        })
        
        if response then
            -- Process response (this handles chat bubbles and actions)
            self:processAIResponse(npc, participant, response)
        end

        -- Clean up thread when done
        for i, threadId in ipairs(self.threadPool.interactionThreads) do
            if threadId == interactionId then
                table.remove(self.threadPool.interactionThreads, i)
                break
            end
        end
    end)
end

function NPCManagerV3:canNPCsInteract(npc1, npc2)
    -- Only check if NPCs exist and are in the same cluster
    if not npc1 or not npc2 then
        return false
    end
    
    -- Use InteractionService to check cluster proximity only
    return self.interactionService:canInteract(npc1, npc2)
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
    
    -- Handle state-specific logic without recursion
    if state == "following" then
        npc.isFollowing = true
        npc.followTarget = data.target
        npc.followStartTime = os.time()
    end
    
    LoggerService:debug("MOVEMENT", string.format(
        "Set %s movement state to %s",
        npc.displayName,
        state
    ))
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

-- Initialize NPC with animations
function NPCManagerV3:initializeNPC(npc)
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if humanoid then
        -- Make sure Animator exists
        if not humanoid:FindFirstChild("Animator") then
            local animator = Instance.new("Animator")
            animator.Parent = humanoid
            LoggerService:debug("NPC", string.format(
                "Created Animator for %s",
                npc.displayName
            ))
        end
        
        AnimationService:applyAnimations(humanoid)
    end
end

-- Add this new function to get all nearby entities
function NPCManagerV3:getClusterMembers(npc)
    local cluster = InteractionService:getClusterForEntity(npc.displayName)
    if not cluster then
        return {}
    end
    
    local members = {}
    for _, memberName in ipairs(cluster.members) do
        if memberName ~= npc.displayName then
            table.insert(members, {
                name = memberName,
                type = memberName == game.Players:GetPlayerFromCharacter(workspace:FindFirstChild(memberName)) and "player" or "npc"
            })
        end
    end
    
    return members
end

-- Update the chat context creation to include nearby entities
function NPCManagerV3:createChatContext(npc, participant)
    local clusterMembers = self:getClusterMembers(npc)
    
    -- Separate into players and NPCs
    local nearbyPlayers = {}
    local nearbyNPCs = {}
    
    for _, entity in ipairs(clusterMembers) do
        if entity.type == "player" then
            table.insert(nearbyPlayers, entity.name)
        elseif entity.type == "npc" then
            table.insert(nearbyNPCs, entity.name)
        end
    end
    
    LoggerService:debug("CHAT", string.format(
        "Found nearby entities for %s: %d players, %d NPCs",
        npc.displayName,
        #nearbyPlayers,
        #nearbyNPCs
    ))
    
    local context = {
        participant_name = participant.Name,
        participant_type = participant:GetParticipantType(),
        participant_id = participant:GetParticipantId(),
        npc_location = npc.currentLocation or "Unknown",
        nearby_players = nearbyPlayers,
        nearby_npcs = nearbyNPCs,
        speaker_name = npc.displayName
    }
    
    return context
end

-- Update the chat handling to refresh proximity data
function NPCManagerV3:handleChat(npc, participant, message)
    LoggerService:info("CHAT", string.format(
        "NPC %s (%s) received message from %s",
        npc.displayName,
        npc.id,
        participant.Name
    ))
    
    -- Refresh proximity data before sending chat
    local context = self:createChatContext(npc, participant)
    
    LoggerService:debug("CHAT", string.format(
        "Created context for %s with %d nearby players and %d nearby NPCs",
        npc.displayName,
        #context.nearby_players,
        #context.nearby_npcs
    ))
    
    -- Create the request
    local request = {
        npc_id = npc.id,
        participant_id = participant:GetParticipantId(),
        message = message,
        context = context
    }
    
    LoggerService:debug("CHAT", string.format(
        "Sending request: %s",
        HttpService:JSONEncode(request)
    ))
    
    return NPCChatHandler:HandleChat(request)
end

function NPCManagerV3:update()
    -- Log proximity matrix every 5 seconds
    if not self._lastProximityLog or 
        (os.clock() - self._lastProximityLog) >= 5 then
        LoggerService:debug("SYSTEM", "Running proximity matrix update...")
        InteractionService:logProximityMatrix(self.npcs)
        self._lastProximityLog = os.clock()
    end
    
    -- Rest of update function...
end

return NPCManagerV3
