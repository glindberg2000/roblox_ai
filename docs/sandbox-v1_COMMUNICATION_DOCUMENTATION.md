# sandbox-v1 Communication System Documentation

Generated: 2024-12-17 06:37:20

## Game Directory Structure

```
├── assets
│   ├── clothings
│   ├── npcs
│   ├── props
│   └── unknown
├── client
│   ├── NPCClientChatHandler.lua
│   └── NPCClientHandler.client.lua
├── data
│   ├── AssetDatabase.lua
│   ├── NPCDatabase.lua
│   └── PlayerDatabase.json
├── server
│   ├── AssetInitializer.server.lua
│   ├── ChatSetup.server.lua
│   ├── InteractionController.lua
│   ├── MainNPCScript.server.lua
│   ├── MockPlayerTest.server.lua
│   ├── NPCInteractionTest.server.lua
│   ├── NPCSystemInitializer.server.lua
│   ├── PlayerJoinHandler.server.lua
│   └── test.server.lua
├── shared
│   ├── NPCSystem
│   │   ├── chat
│   │   │   ├── ChatUtils.lua
│   │   │   ├── NPCChatHandler.lua
│   │   │   ├── V3ChatClient.lua
│   │   │   └── V4ChatClient.lua
│   │   ├── config
│   │   │   ├── InteractionConfig.lua
│   │   │   ├── LettaConfig.lua
│   │   │   ├── NPCConfig.lua
│   │   │   └── PerformanceConfig.lua
│   │   ├── services
│   │   │   ├── AnimationService.lua
│   │   │   ├── InteractionService.lua
│   │   │   ├── LoggerService.lua
│   │   │   ├── ModelLoader.lua
│   │   │   ├── MovementService.lua
│   │   │   └── VisionService.lua
│   │   ├── NPCDatabase.lua
│   │   └── NPCManagerV3.lua
│   ├── AssetModule.lua
│   ├── ChatRouter.lua
│   ├── ConversationManager.lua
│   ├── ConversationManagerV2.lua
│   ├── NPCMovementSystem.lua
│   ├── PerformanceMonitor.lua
│   ├── VisionConfig.lua
│   └── test.lua
└── test
    └── NPCInteractionTest.lua
```

## Communication Files

### server/InteractionController.lua

```lua
-- ServerScriptService/InteractionController.lua
local ServerScriptService = game:GetService("ServerScriptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Wait for critical paths
local Shared = ReplicatedStorage:WaitForChild("Shared")
local NPCSystem = Shared:WaitForChild("NPCSystem")
local services = NPCSystem:WaitForChild("services")

local LoggerService = require(services.LoggerService)
local InteractionService = require(services.InteractionService)

local InteractionController = {}
InteractionController.__index = InteractionController

function InteractionController.new()
    local self = setmetatable({}, InteractionController)
    self.activeInteractions = {}
    LoggerService:log("SYSTEM", "InteractionController initialized")
    return self
end

function InteractionController:startInteraction(player, npc)
    if self.activeInteractions[player] then
        LoggerService:log("PLAYER", string.format("Player %s already in interaction", player.Name))
        return false
    end
    self.activeInteractions[player] = {npc = npc, startTime = tick()}
    LoggerService:log("PLAYER", string.format("Started interaction: %s with %s", player.Name, npc.displayName))
    return true
end

function InteractionController:endInteraction(player)
    LoggerService:log("PLAYER", string.format("Ending interaction for player %s", player.Name))
    self.activeInteractions[player] = nil
end

function InteractionController:canInteract(player)
    return not self.activeInteractions[player]
end

function InteractionController:getInteractingNPC(player)
    local interaction = self.activeInteractions[player]
    return interaction and interaction.npc or nil
end

function InteractionController:getInteractionState(player)
    local interaction = self.activeInteractions[player]
    if interaction then
        return {
            npc_id = interaction.npc.id,
            npc_name = interaction.npc.displayName,
            start_time = interaction.startTime,
            duration = tick() - interaction.startTime,
        }
    end
    return nil
end

function InteractionController:startGroupInteraction(players, npc)
    for _, player in ipairs(players) do
        self.activeInteractions[player] = {npc = npc, group = players, startTime = tick()}
    end
    LoggerService:log("PLAYER", string.format("Started group interaction with %d players", #players))
end

function InteractionController:isInGroupInteraction(player)
    local interaction = self.activeInteractions[player]
    return interaction and interaction.group ~= nil
end

function InteractionController:getGroupParticipants(player)
    local interaction = self.activeInteractions[player]
    if interaction and interaction.group then
        return interaction.group
    end
    return {player}
end

return InteractionController
```

### shared/NPCSystem/NPCManagerV3.lua

```lua
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
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local NPCChatHandler = require(chat:WaitForChild("NPCChatHandler"))
local InteractionService = require(services:WaitForChild("InteractionService"))
local LoggerService = require(services:WaitForChild("LoggerService"))
local ModelLoader = require(script.Parent.services.ModelLoader)
local AnimationService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.AnimationService)

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

    -- Ensure NPCs folder exists
    if not workspace:FindFirstChild("NPCs") then
        Instance.new("Folder", workspace).Name = "NPCs"
        LoggerService:debug("SYSTEM", "Created NPCs folder in workspace")
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
    local humanoid = npc:FindFirstChildOfClass("Humanoid")
    if humanoid then
        AnimationService:applyAnimations(humanoid)
    end
end

return NPCManagerV3

```

### shared/NPCSystem/NPCDatabase.lua

```lua
return {
    npcs = {
        {
            id = "8c9bba8d-4f9a-4748-9e75-1334e48e2e66",
            displayName = "Diamond",
            model = "4446576906",
            spawnPosition = Vector3.new(5, 17, -10),
            responseRadius = 20,
            abilities = {"move", "chat"},
            system_prompt = "You are Diamond, a friendly NPC..."
        },
        -- Other NPCs...
    }
} 
```

### data/NPCDatabase.lua

```lua
return {
    npcs = {
        {
            id = "8c9bba8d-4f9a-4748-9e75-1334e48e2e66", 
            displayName = "Diamond", 
            name = "Diamond", 
            assetId = "4446576906", 
            model = "4446576906", 
            modelName = "Diamond", 
            system_prompt = "I'm sharp as a tack both verbally and emotionally and love wit and humour.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(8.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "e43613f0-cc70-4e98-9b61-2a39fecfa443", 
            displayName = "Goldie", 
            name = "Goldie", 
            assetId = "4446576906", 
            model = "4446576906", 
            modelName = "Goldie", 
            system_prompt = "I'm golden and love luxury and wealth, glamour and glitz.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(10.0, 18.0, -12.0), 
            abilities = {
            "chat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "0544b51c-1009-4231-ac6e-053626135ed4", 
            displayName = "Noobster", 
            name = "Noobster", 
            assetId = "4446576906", 
            model = "4446576906", 
            modelName = "Noobster", 
            system_prompt = "I'm clueless but also can learn fast. I keep on moving in random ways.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(6.0, 18.0, -12.0), 
            abilities = {
            "move", 
            "chat", 
            "trade", 
            "quest", 
            "combat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "3cff63ac-9960-46bb-af7f-88e824d68dbe", 
            displayName = "Oscar", 
            name = "Oscar", 
            assetId = "7315192066", 
            model = "7315192066", 
            modelName = "Oscar", 
            system_prompt = "I am Oscar, twin brother of Pete and I love chasing trouble.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(0.0, 18.0, -6.0), 
            abilities = {
            "chat", 
            "trade", 
            "quest", 
            "combat", 
        }, 
            shortTermMemory = {}, 
        },        {
            id = "693ec89f-40f1-4321-aef9-5aac428f478b", 
            displayName = "Pete", 
            name = "Pete", 
            assetId = "90229749986361", 
            model = "90229749986361", 
            modelName = "Pete", 
            system_prompt = "I am Pete, the proud owner of Pete’s Merch Stand. I have got a knack for finding the coolest stuff—visors, caps, even those iconic Adidas sweats that everyone seems to want. My stand’s got it all, and I like to keep things interesting. If you look closely, you might spot that curious mask hanging behind the tree. Its been with me for a while, and, well, let’s just say its got its secrets. I love talking about my merch—its not just stuff, it’s part of what makes my stand the best place to visit! I can be chatty at times. Im a little sunburned from all the sports I do.", 
            responseRadius = 20, 
            spawnPosition = Vector3.new(-12.5, 18.0, -126.0), 
            abilities = {
            "move", 
            "chat", 
            "initiate_chat", 
            "follow", 
            "unfollow", 
            "run", 
            "jump", 
            "emote", 
        }, 
            shortTermMemory = {}, 
        },
    },
}
```
