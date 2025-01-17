# sandbox-v1 NPC System Documentation (Minimal)

## Game Directory Structure

```
├── assets
│   ├── npcs
│   └── unknown
├── client
│   └── NPCClientHandler.client.lua
├── data
│   ├── AssetDatabase.json
│   ├── AssetDatabase.lua
│   ├── NPCDatabase.json
│   ├── NPCDatabase.lua
│   └── PlayerDatabase.json
├── server
│   ├── AssetInitializer.server.lua
│   ├── ChatSetup.server.lua
│   ├── InteractionController.lua
│   ├── Logger.lua
│   ├── MainNPCScript.lua
│   ├── MainNPCScript.server.lua
│   ├── MockPlayer.lua
│   ├── MockPlayerTest.server.lua
│   ├── NPCConfigurations.lua
│   ├── NPCInteractionTest.lua
│   ├── NPCInteractionTest.server.lua
│   ├── NPCSystemInitializer.server.lua
│   └── PlayerJoinHandler.server.lua
└── shared
    ├── AnimationManager.lua
    ├── AssetModule.lua
    ├── ChatUtils.lua
    ├── ConversationManagerV2.lua
    ├── NPCChatHandler.lua
    ├── NPCConfig.lua
    ├── NPCManagerV3.lua
    ├── V3ChatClient.lua
    └── V4ChatClient.lua
```

## API Directory Structure

```
├── app
│   ├── __init__.py
│   ├── ai_handler.py
│   ├── config.py
│   ├── conversation_manager.py
│   ├── conversation_managerV2.py
│   ├── dashboard_router.py
│   ├── database.py
│   ├── db.py
│   ├── image_utils.py
│   ├── main.py
│   ├── middleware.py
│   ├── models.py
│   ├── paths.py
│   ├── routers.py
│   ├── routers_v4.py
│   ├── security.py
│   ├── singletons.py
│   ├── storage.py
│   ├── tasks.py
│   └── utils.py
├── db
│   ├── migrate.py
│   ├── schema.sql
├── initial_data
│   └── game1
│       └── src
│           └── data
│               ├── AssetDatabase.json
│               └── NPCDatabase.json
├── modules
│   └── game_creator.py
├── routes
│   └── games.py
├── static
│   ├── css
│   │   └── dashboard.css
│   └── js
│       ├── dashboard_new
│       │   ├── abilityConfig.js
│       │   ├── assets.js
│       │   ├── game.js
│       │   ├── games.js
│       │   ├── index.js
│       │   ├── npc.js
│       │   ├── state.js
│       │   ├── ui.js
│       │   └── utils.js
│       ├── abilityConfig.js
│       ├── dashboard.js
│       └── games.js
├── storage
│   ├── assets
│   │   ├── models
│   │   ├── thumbnails
│   ├── avatars
│   ├── default
│   │   ├── assets
│   │   ├── avatars
│   │   └── thumbnails
│   └── thumbnails
├── templates
│   ├── dashboard_new.html
│   ├── npc-edit.html
│   ├── npcs.html
│   └── players.html
├── .env.example
├── init_db.py
├── pytest.ini
├── requirements.txt
├── setup_db.py
├── test_imports.py
└── testimg.py
```

## Core Game Files

### shared/NPCChatHandler.lua

```lua
-- NPCChatHandler.lua
local NPCChatHandler = {}

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V4ChatClient = require(ReplicatedStorage.NPCSystem.V4ChatClient)
local V3ChatClient = require(ReplicatedStorage.NPCSystem.V3ChatClient)
local HttpService = game:GetService("HttpService")

function NPCChatHandler:HandleChat(request)
    print("NPCChatHandler: Received request", HttpService:JSONEncode(request))
    
    -- Try V4 first
    print("NPCChatHandler: Attempting V4")
    local response = V4ChatClient:SendMessage(request)
    
    -- Fall back to V3 if needed
    if not response.success and response.shouldFallback then
        print("NPCChatHandler: Falling back to V3", response.error)
        return V3ChatClient:SendMessage(request)
    end
    
    print("NPCChatHandler: V4 succeeded", HttpService:JSONEncode(response))
    return response
end

return NPCChatHandler 
```

### shared/NPCManagerV3.lua

```lua
-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local ChatService = game:GetService("Chat")

local AnimationManager = require(ReplicatedStorage.Shared.AnimationManager)
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))
local NPCChatHandler = require(ReplicatedStorage.NPCSystem.NPCChatHandler)

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
        instance.activeInteractions = {} -- Track ongoing interactions
        instance.movementStates = {} -- Track movement states per NPC
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

-- Add handler for player messages at initialization
NPCChatEvent.OnServerEvent:Connect(function(player, data)
    NPCManagerV3:getInstance():handlePlayerMessage(player, data)
end)

function NPCManagerV3:handlePlayerMessage(player, data)
    local npcName = data.npcName
    local message = data.message
    
    Logger:log("CHAT", string.format("Received message from player %s to NPC %s: %s",
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
                Logger:log("INTERACTION", string.format("NPC %s is not interacting with player %s", 
                    npc.displayName, 
                    player.Name
                ))
            end
            return
        end
    end
    
    Logger:log("ERROR", string.format("NPC %s not found when handling player message", npcName))
end

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
    
    -- Return the created NPC
    return npc
end

-- Add a separate function to test chat for all NPCs
function NPCManagerV3:testAllNPCChat()
    Logger:log("TEST", "Testing chat for all NPCs...")
    for _, npc in pairs(self.npcs) do
        if npc.model and npc.model:FindFirstChild("Head") then
            -- Try simple chat method only
            game:GetService("Chat"):Chat(npc.model.Head, "Test chat from " .. npc.displayName)
            wait(0.5) -- Small delay between tests
        end
    end
    Logger:log("TEST", "Chat testing complete")
end

-- Update loadNPCDatabase to run chat test after all NPCs are created
function NPCManagerV3:loadNPCDatabase()
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    Logger:log("DATABASE", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
    for _, npcData in ipairs(npcDatabase.npcs) do
        self:createNPC(npcData)
    end
    
    -- Test chat after all NPCs are created
    wait(1) -- Give a moment for everything to settle
    self:testAllNPCChat()
end

-- Modify the createNPC function to initialize chat speaker
-- Store the original createNPC function
local originalCreateNPC = NPCManagerV3.createNPC

-- Override createNPC to add chat speaker initialization
function NPCManagerV3:createNPC(npcData)
    local npc = originalCreateNPC(self, npcData)
    if npc then
        self:initializeNPCChatSpeaker(npc)
    end
    return npc
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



function NPCManagerV3:endInteraction(npc, participant, interactionId)
    Logger:log("INTERACTION", string.format("Pausing interaction for %s with %s (ID: %s)",
        npc.displayName,
        participant and participant.Name or "Unknown",
        interactionId or "N/A"
    ))

    -- Update timestamps
    npc.lastInteractionTime = tick()
    npc.lastConversationTime = tick()
    
    if participant then
        npc.lastInteractionPartner = typeof(participant) == "Instance" and participant.UserId or participant.npcId
    end

    -- Preserve conversation context and history
    if npc.currentConversationId then
        Logger:log("CHAT", string.format("Preserving conversation %s for %s with %s",
            npc.currentConversationId,
            npc.displayName,
            participant.Name or participant.displayName
        ))
    end

    -- Clean up interaction tracking
    if interactionId then
        self.activeInteractions[interactionId] = nil
    end

    -- Free movement state but preserve conversation data
    self:setNPCMovementState(npc, "free")
    npc.isInteracting = false
    npc.interactingPlayer = nil

    -- Handle NPC-to-NPC cleanup
    if self:isNPCParticipant(participant) then
        local otherNPC = self.npcs[participant.npcId]
        if otherNPC then
            self:setNPCMovementState(otherNPC, "free")
            otherNPC.isInteracting = false
            otherNPC.interactingPlayer = nil
        end
    end

    -- Notify client of paused conversation
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        NPCChatEvent:FireClient(participant, {
            npcName = npc.displayName,
            type = "paused_conversation",
            conversationId = npc.currentConversationId
        })
    end
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
-- Replace the isNPCParticipant function with this improved version
function NPCManagerV3:isNPCParticipant(participant)
    if not participant then return false end
    
    -- Check if it's a Player instance
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        Logger:log("PARTICIPANT", "Participant is a Player instance")
        return false
    end
    
    -- Check if it's a mock NPC participant or has NPC-specific properties
    if participant.npcId or participant.Type == "npc" then
        Logger:log("PARTICIPANT", string.format("Participant is an NPC with ID: %s", participant.npcId))
        return true
    end
    
    Logger:log("PARTICIPANT", "Participant is neither Player nor NPC")
    return false
end

function NPCManagerV3:displayMessage(npc, message, recipient)
    -- Handle player messages
    if typeof(recipient) == "Instance" and recipient:IsA("Player") then
        Logger:log("CHAT", string.format("NPC %s sending message to player %s: %s",
            npc.displayName,
            recipient.Name,
            message
        ))
        
        -- Create chat bubble
        if npc.model and npc.model:FindFirstChild("Head") then
            game:GetService("Chat"):Chat(npc.model.Head, message)
            Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
        end
        
        -- Send to player's chat window
        NPCChatEvent:FireClient(recipient, {
            npcName = npc.displayName,
            message = message,
            type = "chat"
        })
        
        -- Record in chat history
        table.insert(npc.chatHistory, {
            sender = npc.displayName,
            recipient = recipient.Name,
            message = message,
            timestamp = os.time()
        })
        return
    end
    
    -- Handle NPC-to-NPC messages
    if self:isNPCParticipant(recipient) then
        Logger:log("CHAT", string.format("NPC %s to NPC %s: %s",
            npc.displayName,
            recipient.displayName or recipient.Name,
            message
        ))
        
        -- Create chat bubble
        if npc.model and npc.model:FindFirstChild("Head") then
            game:GetService("Chat"):Chat(npc.model.Head, message)
            Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", npc.displayName))
        end
        
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
                -- Continue conversation if they share the same conversation ID
                if not recipientNPC.currentConversationId or recipientNPC.currentConversationId == npc.currentConversationId then
                    task.delay(1, function()
                        -- Share the same conversation ID
                        recipientNPC.currentConversationId = npc.currentConversationId
                        self:handleNPCInteraction(recipientNPC, self:createMockParticipant(npc), message)
                    end)
                end
            end
        end
        return
    end
    
    -- Log if recipient type is unknown
    Logger:log("ERROR", string.format("Unknown recipient type for message from %s", npc.displayName))
end

-- And modify processAIResponse to directly use displayMessage
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
        -- Use displayMessage directly
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


-- Add this new function to help manage NPC chat speakers
function NPCManagerV3:initializeNPCChatSpeaker(npc)
    if npc and npc.model then
        local createSpeaker = _G.CreateNPCSpeaker
        if createSpeaker then
            createSpeaker(npc.model)
            Logger:log("SYSTEM", string.format("Initialized chat speaker for NPC: %s", npc.displayName))
        end
    end
end

-- Update the displayNPCToNPCMessage function in NPCManagerV3.lua
function NPCManagerV3:testChatBubbles(fromNPC)
    if not fromNPC or not fromNPC.model then
        Logger:log("ERROR", "Invalid NPC for chat test")
        return
    end

    local head = fromNPC.model:FindFirstChild("Head")
    if not head then
        Logger:log("ERROR", string.format("NPC %s has no Head part!", fromNPC.displayName))
        return
    end

    -- Try each chat method
    Logger:log("TEST", "Testing chat methods...")

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
        Logger:log("ERROR", "ChatService method failed: " .. tostring(err))
    end

    Logger:log("TEST", "Chat test complete")
end

-- Also update displayNPCToNPCMessage to try all methods
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
    
    -- Use the same direct Chat call that worked in our test
    if fromNPC.model and fromNPC.model:FindFirstChild("Head") then
        game:GetService("Chat"):Chat(fromNPC.model.Head, message)
        Logger:log("CHAT", string.format("Created chat bubble for NPC: %s", fromNPC.displayName))
    end
    
    -- Fire event to all clients for redundancy
    NPCChatEvent:FireAllClients({
        npcName = fromNPC.displayName,
        message = message,
        type = "npc_chat"
    })
end

function NPCManagerV3:executeAction(npc, player, action)
    Logger:log("ACTION", string.format("Executing action: %s for %s", action.type, npc.displayName))
    
    if action.type == "stop_talking" then
        -- Stop following if we were following this player
        if npc.isFollowing and npc.followTarget == player then
            Logger:log("MOVEMENT", string.format("Stopping follow as part of ending interaction: %s", player.Name))
            self:stopFollowing(npc)
        end
        -- Let the normal conversation flow handle the ending
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
    npc.isFollowing = true
    npc.followTarget = player
    npc.followStartTime = tick()
    npc.isWalking = false  -- Will be set to true when movement starts
    -- Ensure NPC can move while following
    self:setNPCMovementState(npc, "following")
    Logger:log("STATE", string.format("Follow state set for %s: isFollowing=%s, followTarget=%s",
        npc.displayName,
        tostring(npc.isFollowing),
        tostring(player.Name)
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

function NPCManagerV3:handleNPCInteraction(npc, participant, message)
    -- First check if this is a valid participant
    if not npc or not participant then
        Logger:warn("Invalid participants in handleNPCInteraction")
        return
    end

    -- Generate participant ID
    local participantId = typeof(participant) == "Instance" and participant.UserId or participant.npcId
    
    -- Check for existing conversation timeout
    if npc.lastConversationTime and npc.currentConversationId then
        local timeSinceLastChat = tick() - npc.lastConversationTime
        if timeSinceLastChat > 1800 then -- 30 minutes
            Logger:log("CHAT", string.format("Clearing old conversation context %s for %s (inactive for %.0f seconds)",
                npc.currentConversationId,
                npc.displayName,
                timeSinceLastChat
            ))
            npc.currentConversationId = nil
            npc.hasGreetedParticipant = nil
            npc.chatHistory = {} -- Clear chat history when conversation expires
        end
    end

    -- Handle greeting logic
    local isNewConversation = not npc.currentConversationId
    local isGreeting = message == "Hello"

    -- If we have an existing conversation, transform greeting to continuation
    if isGreeting and not isNewConversation then
        -- Check if this is a quick re-engagement (within 5 minutes)
        local timeSinceLastChat = tick() - (npc.lastConversationTime or 0)
        if timeSinceLastChat <= 300 then -- 5 minutes
            -- Transform greeting to continuation
            message = "Hi again!"
            Logger:log("CHAT", string.format("Transformed greeting to continuation for recent conversation %s", 
                npc.currentConversationId
            ))
        else
            -- Treat as new conversation if it's been a while
            npc.currentConversationId = nil
            isNewConversation = true
            Logger:log("CHAT", "Starting new conversation after long pause")
        end
    end

    -- Skip duplicate greetings with cooldown
    if isGreeting and npc.hasGreetedParticipant == participantId then
        local timeSinceLastGreeting = tick() - (npc.lastGreetingTime or 0)
        if timeSinceLastGreeting < 30 then -- 30 second cooldown
            Logger:log("INTERACTION", string.format("Skipping duplicate greeting from %s (cooldown: %.1f seconds)", 
                participant.Name or participant.displayName,
                timeSinceLastGreeting
            ))
            return
        end
    end

    -- Generate interaction ID
    local interactionId = HttpService:GenerateGUID(false)
    
    -- Update interaction history
    npc.chatHistory = npc.chatHistory or {}
    table.insert(npc.chatHistory, {
        sender = participant.Name or participant.displayName,
        message = message,
        timestamp = os.time()
    })

    -- Update greeting state for new conversations only
    if isNewConversation and isGreeting then
        npc.hasGreetedParticipant = participantId
        npc.lastGreetingTime = tick()
    end

    -- Get AI response
    local response = NPCChatHandler:HandleChat({
        message = message,
        player_id = participantId,
        npc_id = npc.id,
        npc_name = npc.displayName,
        system_prompt = npc.system_prompt,
        metadata = npc.currentConversationId and {
            conversation_id = npc.currentConversationId
        } or nil,
        context = {
            participant_type = self:isNPCParticipant(participant) and "npc" or "player",
            participant_name = participant.Name or participant.displayName,
            is_new_conversation = isNewConversation,
            interaction_history = npc.chatHistory,
            nearby_players = self:getVisiblePlayers(npc),
            npc_location = "Unknown"
        },
        perception = self:getPerceptionData(npc)
    })

    if not response then
        Logger:warn("Failed to get AI response, aborting interaction")
        return
    end

    -- Update conversation state and timestamp
    if response.metadata and response.metadata.conversation_id then
        npc.currentConversationId = response.metadata.conversation_id
        npc.lastConversationTime = tick()
        
        -- Store response in chat history
        table.insert(npc.chatHistory, {
            sender = npc.displayName,
            recipient = participant.Name or participant.displayName,
            message = response.message,
            timestamp = os.time()
        })
    end

    -- Handle different interaction types
    if typeof(participant) == "Instance" and participant:IsA("Player") then
        self:handlePlayerInteraction(npc, participant, message, interactionId)
    elseif self:isNPCParticipant(participant) then
        self:handleNPCToNPCInteraction(npc, participant, message, interactionId)
    end

    -- Process the response
    self:processAIResponse(npc, participant, response)
end

function NPCManagerV3:handlePlayerInteraction(npc, player, message, interactionId)
    -- Lock only the NPC, not the player
    self:setNPCMovementState(npc, "locked", interactionId)
    
    -- Update NPC state
    npc.isInteracting = true
    npc.interactingPlayer = player

    -- Fire client event for chat window
    NPCChatEvent:FireClient(player, {
        npcName = npc.displayName,
        message = message,
        type = "started_conversation"
    })
end

function NPCManagerV3:handleNPCToNPCInteraction(npc1, npc2Participant, message, interactionId)
    local npc2 = self.npcs[npc2Participant.npcId]
    if not npc2 then 
        Logger:warn("Could not find NPC2 for interaction")
        return 
    end

    -- Generate interaction ID if not provided
    interactionId = interactionId or HttpService:GenerateGUID(false)
    Logger:log("INTERACTION", string.format("Starting NPC interaction between %s and %s (ID: %s)",
        npc1.displayName,
        npc2.displayName,
        interactionId
    ))

    -- Only lock NPCs if they're not already in an interaction
    if not npc1.isInteracting and not npc2.isInteracting then
        self:setNPCMovementState(npc1, "locked", interactionId)
        self:setNPCMovementState(npc2, "locked", interactionId)

        npc1.isInteracting = true
        npc2.isInteracting = true
        npc1.interactingPlayer = npc2Participant
        npc2.interactingPlayer = self:createMockParticipant(npc1)
        
        -- Track active interaction
        self.activeInteractions[interactionId] = {
            npc1 = npc1,
            npc2 = npc2,
            startTime = tick()
        }
    end
end

function NPCManagerV3:setNPCMovementState(npc, state, interactionId)
    if not npc or not npc.model then return end
    
    Logger:log("STATE", string.format("Setting %s movement state: %s -> %s (interactionId: %s)", 
        npc.displayName,
        npc.movementState or "unknown",
        state,
        interactionId or "none"
    ))

    if state == "following" then
        npc.model.Humanoid.WalkSpeed = 16
        npc.movementState = "following"
        Logger:log("MOVEMENT", string.format("%s is now following with speed %d", npc.displayName, npc.model.Humanoid.WalkSpeed))
    elseif state == "locked" and interactionId then
        npc.model.Humanoid.WalkSpeed = 0
        npc.isInteracting = true
        npc.interactionId = interactionId
        npc.movementState = "locked"
        Logger:log("LOCK", string.format("Locked %s for interaction %s", npc.displayName, interactionId))
    else
        npc.model.Humanoid.WalkSpeed = 16
        npc.isInteracting = false
        npc.interactionId = nil
        npc.interactingPlayer = nil
        npc.movementState = "free"
        Logger:log("UNLOCK", string.format("Freed %s from previous state", npc.displayName))
    end
end

function NPCManagerV3:cleanupStaleInteractions()
    local currentTime = tick()
    local staleThreshold = 300 -- 5 minutes

    for interactionId, interaction in pairs(self.activeInteractions) do
        if currentTime - interaction.lastUpdateTime > staleThreshold then
            Logger:warn(string.format("Cleaning up stale interaction: %s", interactionId))
            self:endInteraction(interaction.npc, interaction.participant, interactionId)
        end
    end
end

function NPCManagerV3:updateNPCState(npc)
    if not npc.model or not npc.model.PrimaryPart then return end
    
    self:updateNPCVision(npc)
    
    local humanoid = npc.model:FindFirstChild("Humanoid")
    if not humanoid then return end

    -- Handle following behavior
    if npc.isFollowing and npc.followTarget then
        local targetCharacter = npc.followTarget.Character
        if targetCharacter and targetCharacter:FindFirstChild("HumanoidRootPart") then
            local targetPosition = targetCharacter.HumanoidRootPart.Position
            local npcPosition = npc.model.PrimaryPart.Position
            local distance = (targetPosition - npcPosition).Magnitude
            
            -- Only move if we're too far from target
            if distance > MIN_FOLLOW_DISTANCE then
                -- Calculate target point (slightly behind the player)
                local direction = (targetPosition - npcPosition).Unit
                local targetPoint = targetPosition - direction * MIN_FOLLOW_DISTANCE
                
                -- Move NPC
                humanoid:MoveTo(targetPoint)
                
                -- Play walk animation if not already playing
                if npc.movementState == "following" and not npc.isWalking then
                    npc.isWalking = true
                    AnimationManager:playAnimation(humanoid, "walk")
                end
                
                Logger:log("MOVEMENT", string.format("%s following %s at distance %.1f", 
                    npc.displayName,
                    npc.followTarget.Name,
                    distance
                ))
            else
                -- Stop walking animation if we're close enough
                if npc.isWalking then
                    npc.isWalking = false
                    AnimationManager:playAnimation(humanoid, "idle")
                end
            end
        end
        -- Skip other checks while following
        return
    end

    -- Check if the NPC should be freed from interaction
    if npc.isInteracting then
        if npc.interactingPlayer then
            local shouldEndInteraction = false
            
            if self:isNPCParticipant(npc.interactingPlayer) then
                -- For NPC-to-NPC, check if other NPC is still valid/interacting
                local otherNPC = self.npcs[npc.interactingPlayer.npcId]
                if not otherNPC or not otherNPC.isInteracting then
                    shouldEndInteraction = true
                end
            else
                -- For player interactions, check range
                if not self:isPlayerInRange(npc, npc.interactingPlayer) then
                    shouldEndInteraction = true
                end
            end
            
            if shouldEndInteraction then
                self:endInteraction(npc, npc.interactingPlayer)
            end
        end
    end
end

function NPCManagerV3:isPlayerInRange(npc, player)
    if not player or not player.Character then return false end
    if not npc.model or not npc.model.PrimaryPart then return false end

    -- Skip range check if following this player
    if npc.isFollowing and npc.followTarget == player then
        return true
    end

    -- Check if we recently ended an interaction with this player
    local currentTime = tick()
    if npc.lastInteractionTime and npc.lastInteractionPartner == player.UserId then
        local timeSinceLastInteraction = currentTime - npc.lastInteractionTime
        if timeSinceLastInteraction < 30 then -- 30 second cooldown
            return false
        end
    end

    local distance = (npc.model.PrimaryPart.Position - player.Character.PrimaryPart.Position).Magnitude
    return distance <= npc.responseRadius
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

    local currentTime = tick()

    -- Add an initial spawn delay
    if not npc.spawnTime then
        npc.spawnTime = currentTime
        Logger:log("SPAWN", string.format("Set initial spawn time for %s", npc.displayName))
        return
    end

    -- Skip interactions during the initial spawn delay
    if currentTime - npc.spawnTime < 5 then
        return
    end

    -- Existing cooldown logic
    if (currentTime - (npc.lastInteractionTime or 0)) < 30 then
        return
    end

    Logger:log("INTERACTION_CHECK", string.format("Checking interactions for %s", npc.displayName))

    -- Now check for nearby NPCs to interact with
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



function NPCManagerV3:getResponseFromAI(npc, participant, message)
    -- Ensure we're using the correct participant name
    local participantName = participant.Name or participant.displayName or "Unknown"

    local participantType = self:isNPCParticipant(participant) and "npc" or "player"
    local playerId
    if participantType == "npc" then
        playerId = "npc_" .. participant.npcId
    else
        playerId = tostring(participant.UserId)
    end

    -- Check if this is a continuation of a conversation
    local isNewConversation = not npc.currentConversationId
    if not isNewConversation then
        Logger:log("CHAT", string.format("Continuing conversation %s with %s", 
            npc.currentConversationId,
            participantName
        ))
    end

    local data = {
        message = message,
        player_id = playerId,
        npc_id = npc.id,
        npc_name = npc.displayName,
        participant_name = participantName,
        system_prompt = npc.system_prompt,
        perception = self:getPerceptionData(npc),
        metadata = npc.currentConversationId and {
            conversation_id = npc.currentConversationId
        } or nil,
        context = {
            participant_type = participantType,
            participant_name = participantName,
            is_new_conversation = isNewConversation,
            interaction_history = npc.chatHistory or {},
            nearby_players = self:getVisiblePlayers(npc),
            npc_location = "Unknown"
        },
        memory = npc.shortTermMemory[playerId] or {}
    }

    local success, response = pcall(function()
        return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
    end)

    if success then
        Logger:log("API", string.format("Raw API response for interaction between %s and %s: %s", 
            npc.displayName,
            participantName,
            response
        ))
        local parsed = HttpService:JSONDecode(response)
        if parsed and parsed.message then
            self.responseCache[self:getCacheKey(npc, participant, message)] = parsed
            npc.shortTermMemory[playerId] = {
                lastInteractionTime = tick(),
                recentTopics = parsed.topics_discussed or {},
                participantName = participantName
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


```

### shared/AnimationManager.lua

```lua
local AnimationManager = {}
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

local animations = {
    walk = "rbxassetid://180426354", -- Replace with your walk animation asset ID
    jump = "rbxassetid://125750702", -- Replace with your jump animation asset ID
    idle = "rbxassetid://507766388", -- Replace with your idle animation asset ID
}

-- Table to store animations per humanoid
local animationTracks = {}

-- Apply animations to NPC's humanoid
function AnimationManager:applyAnimations(humanoid)
    if not humanoid then
        Logger:log("ERROR", "Cannot apply animations: Humanoid is nil")
        return
    end

    local animator = humanoid:FindFirstChild("Animator") or Instance.new("Animator", humanoid)

    -- Initialize animationTracks for this humanoid
    animationTracks[humanoid] = {}

    -- Preload animations
    for name, id in pairs(animations) do
        local animation = Instance.new("Animation")
        animation.AnimationId = id

        local animationTrack = animator:LoadAnimation(animation)
        animationTracks[humanoid][name] = animationTrack
        Logger:log("ANIMATION", string.format("Loaded animation '%s' for humanoid: %s", 
            name, 
            humanoid.Parent.Name
        ))
    end

    Logger:log("ANIMATION", string.format("Animations applied to humanoid: %s", humanoid.Parent.Name))
end

-- Play a specific animation
function AnimationManager:playAnimation(humanoid, animationName)
    if animationTracks[humanoid] and animationTracks[humanoid][animationName] then
        Logger:log("ANIMATION", string.format("Playing animation '%s' for humanoid: %s", 
            animationName, 
            humanoid.Parent.Name
        ))
        animationTracks[humanoid][animationName]:Play()
    else
        Logger:log("ERROR", string.format("No animation track found: %s for humanoid: %s", 
            animationName, 
            humanoid and humanoid.Parent and humanoid.Parent.Name or "unknown"
        ))
    end
end

-- Stop all animations
function AnimationManager:stopAnimations(humanoid)
    if animationTracks[humanoid] then
        for name, track in pairs(animationTracks[humanoid]) do
            track:Stop()
            Logger:log("ANIMATION", string.format("Stopped animation '%s' for humanoid: %s", 
                name, 
                humanoid.Parent.Name
            ))
        end
    end
end

return AnimationManager
```

## Core API Files

### app/models.py

```py
# app/models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal

class NPCAction(BaseModel):
    type: Literal["follow", "unfollow", "stop_talking", "none"]
    data: Optional[Dict[str, Any]] = None

class NPCResponseV3(BaseModel):
    message: str
    action: NPCAction
    internal_state: Optional[Dict[str, Any]] = None

class PerceptionData(BaseModel):
    visible_objects: List[str] = Field(default_factory=list)
    visible_players: List[str] = Field(default_factory=list)
    memory: List[Dict[str, Any]] = Field(default_factory=list)

class EnhancedChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    initiator_id: str
    target_id: str
    conversation_type: Literal["npc_user", "npc_npc", "group"]
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    system_prompt: str

class ConversationResponse(BaseModel):
    conversation_id: str
    message: str
    action: NPCAction
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationMetrics:
    def __init__(self):
        self.total_conversations = 0
        self.active_conversations = 0
        self.completed_conversations = 0
        self.average_response_time = 0.0
        self.total_messages = 0
        
    @property
    def dict(self):
        return self.model_dump()
        
    def model_dump(self):
        return {
            "total_conversations": self.total_conversations,
            "active_conversations": self.active_conversations,
            "completed_conversations": self.completed_conversations,
            "average_response_time": self.average_response_time,
            "total_messages": self.total_messages
        }
```

### app/routers_v4.py

```py
# app/routers_v4.py

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import os

from .models import (
    EnhancedChatRequest, 
    ConversationResponse, 
    NPCResponseV3, 
    NPCAction
)
from .ai_handler import AIHandler
from .conversation_managerV2 import ConversationManagerV2
from .config import NPC_SYSTEM_PROMPT_ADDITION

# Initialize logging
logger = logging.getLogger("ella_app")

# Initialize router with v4 prefix
router = APIRouter(prefix="/v4")

# Initialize managers
conversation_manager = ConversationManagerV2()
ai_handler = AIHandler(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat")
async def enhanced_chat_endpoint(request: EnhancedChatRequest):
    """
    Enhanced chat endpoint supporting different conversation types
    and persistent conversation state
    """
    try:
        logger.info(f"V4 Chat request: {request.conversation_type} from {request.initiator_id}")

        # Validate conversation type
        if request.conversation_type not in ["npc_user", "npc_npc", "group"]:
            raise HTTPException(status_code=422, detail="Invalid conversation type")

        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create participants with appropriate types based on conversation_type
            initiator_data = {
                "id": request.initiator_id,
                "type": "npc" if request.conversation_type.startswith("npc") else "player",
                "name": request.context.get("initiator_name", f"Entity_{request.initiator_id}")
            }
            
            target_data = {
                "id": request.target_id,
                "type": "npc" if request.conversation_type.endswith("npc") else "player",
                "name": request.context.get("target_name", f"Entity_{request.target_id}")
            }
            
            # Create Participant objects before passing to create_conversation
            conversation_id = conversation_manager.create_conversation(
                type=request.conversation_type,
                participant1_data=initiator_data,
                participant2_data=target_data
            )
            
            if not conversation_id:
                raise HTTPException(
                    status_code=429,
                    detail="Cannot create new conversation - rate limit or participant limit reached"
                )

        # Get conversation history
        history = conversation_manager.get_history(conversation_id)
        
        # Prepare context for AI
        context_summary = f"""
        Conversation type: {request.conversation_type}
        Initiator: {request.context.get('initiator_name', request.initiator_id)}
        Target: {request.context.get('target_name', request.target_id)}
        """

        if request.context:
            context_details = "\n".join(f"{k}: {v}" for k, v in request.context.items() 
                                      if k not in ['initiator_name', 'target_name'])
            if context_details:
                context_summary += f"\nAdditional context:\n{context_details}"

        # Prepare messages for AI
        messages = [
            {"role": "system", "content": f"{request.system_prompt}\n\n{NPC_SYSTEM_PROMPT_ADDITION}\n\nContext: {context_summary}"},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg} 
              for i, msg in enumerate(history)],
            {"role": "user", "content": request.message}
        ]

        # Mock AI response for testing
        if os.getenv("TESTING"):
            response = NPCResponseV3(
                message="Test response",
                action=NPCAction(type="none")
            )
        else:
            response = await ai_handler.get_response(
                messages=messages,
                system_prompt=request.system_prompt
            )

        # Add messages to conversation history
        conversation_manager.add_message(
            conversation_id,
            request.initiator_id,
            request.message
        )
        
        if response.message:
            conversation_manager.add_message(
                conversation_id,
                request.target_id,
                response.message
            )

        # Check for conversation end
        if response.action and response.action.type == "stop_talking":
            conversation_manager.end_conversation(conversation_id)
            logger.info(f"Ending conversation {conversation_id} due to stop_talking action")

        # Get conversation metadata
        metadata = conversation_manager.get_conversation_context(conversation_id)

        return ConversationResponse(
            conversation_id=conversation_id,
            message=response.message,
            action=NPCAction(type=response.action.type, data=response.action.data or {}),
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Error in v4 chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def end_conversation_endpoint(conversation_id: str):
    """Manually end a conversation"""
    try:
        conversation_manager.end_conversation(conversation_id)
        return JSONResponse({"status": "success", "message": "Conversation ended"})
    except Exception as e:
        logger.error(f"Error ending conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{participant_id}")
async def get_participant_conversations(participant_id: str):
    """Get all active conversations for a participant"""
    try:
        conversations = conversation_manager.get_active_conversations(participant_id)
        return JSONResponse({
            "participant_id": participant_id,
            "conversations": [
                conversation_manager.get_conversation_context(conv_id)
                for conv_id in conversations
            ]
        })
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics():
    """Get conversation metrics"""
    return JSONResponse({
        "conversation_metrics": conversation_manager.metrics.dict()
    })
```

### app/ai_handler.py

```py
# app/ai_handler.py

import asyncio
import logging
import json
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger("ella_app")

class NPCAction(BaseModel):
    type: str = Field(..., pattern="^(follow|unfollow|stop_talking|none)$")
    data: Dict[str, Any] = Field(default_factory=dict)

class NPCResponse(BaseModel):
    message: str
    action: NPCAction
    internal_state: Dict[str, Any] = Field(default_factory=dict)

class AIHandler:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.response_cache = {}
        self.max_parallel_requests = 5
        self.semaphore = asyncio.Semaphore(self.max_parallel_requests)

        # Define the response schema once
        self.response_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "npc_response",
                "description": "NPC response format including message and action",
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The NPC's spoken response"
                        },
                        "action": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["follow", "unfollow", "stop_talking", "none"],
                                    "description": "The type of action to take"
                                },
                                "data": {
                                    "type": "object"
                                }
                            },
                            "required": ["type"]
                        },
                        "internal_state": {
                            "type": "object"
                        }
                    },
                    "required": ["message", "action"]
                }
            }
        }

    async def get_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_tokens: int = 200
    ) -> NPCResponse:
        """Get structured response from OpenAI"""
        try:
            async with self.semaphore:
                completion = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *messages
                    ],
                    max_tokens=max_tokens,
                    response_format=self.response_schema,
                    temperature=0.7
                )

                # Check for refusal
                if hasattr(completion.choices[0].message, 'refusal') and completion.choices[0].message.refusal:
                    logger.warning("AI refused to respond")
                    return NPCResponse(
                        message="I cannot respond to that request.",
                        action=NPCAction(type="none")
                    )

                # Check for incomplete response
                if completion.choices[0].finish_reason != "stop":
                    logger.warning(f"Response incomplete: {completion.choices[0].finish_reason}")
                    return NPCResponse(
                        message="I apologize, but I was unable to complete my response.",
                        action=NPCAction(type="none")
                    )

                # Parse the response into our Pydantic model
                response_data = completion.choices[0].message.content
                logger.debug(f"Raw AI response: {response_data}")
                
                return NPCResponse(**json.loads(response_data))

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
            return NPCResponse(
                message="Hello! How can I help you today?",
                action=NPCAction(type="none")
            )

    async def process_parallel_responses(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[NPCResponse]:
        """Process multiple requests in parallel"""
        tasks = [
            self.get_response(
                req["messages"],
                req["system_prompt"],
                req.get("max_tokens", 200)
            )
            for req in requests
        ]
        
        return await asyncio.gather(*tasks)
```

### app/conversation_managerV2.py

```py
# app/conversation_managerV2.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, ConfigDict
from .models import ConversationMetrics
import uuid
import logging

logger = logging.getLogger("roblox_app")

class Participant(BaseModel):
    id: str
    type: Literal["npc", "player"]
    name: str

class Message(BaseModel):
    sender_id: str
    content: str
    timestamp: datetime

class Conversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    type: Literal["npc_user", "npc_npc", "group"]
    participants: Dict[str, Participant]
    messages: List[Message]
    created_at: datetime
    last_update: datetime
    metadata: Dict[str, Any] = {}

class ConversationMetrics:
    def __init__(self):
        self.total_conversations = 0
        self.successful_conversations = 0
        self.failed_conversations = 0
        self.average_duration = 0.0
        self.active_conversations = 0
        self.completed_conversations = 0
        self.average_response_time = 0.0
        self.total_messages = 0

    def dict(self):
        return {
            "total_conversations": self.total_conversations,
            "successful_conversations": self.successful_conversations,
            "failed_conversations": self.failed_conversations,
            "average_duration": self.average_duration,
            "active_conversations": self.active_conversations,
            "completed_conversations": self.completed_conversations,
            "average_response_time": self.average_response_time,
            "total_messages": self.total_messages
        }

class ConversationManagerV2:
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.participant_conversations: Dict[str, List[str]] = {}
        self.expiry_time = timedelta(minutes=30)
        self.metrics = ConversationMetrics()

    def create_conversation(
        self,
        type: Literal["npc_user", "npc_npc", "group"],
        participant1_data: Dict[str, Any],
        participant2_data: Dict[str, Any]
    ) -> str:
        """Create a new conversation between participants"""
        try:
            # Create Participant objects from dictionaries
            participant1 = Participant(
                id=participant1_data["id"],
                type=participant1_data.get("type", "npc"),
                name=participant1_data.get("name", f"Entity_{participant1_data['id']}")
            )
            
            participant2 = Participant(
                id=participant2_data["id"],
                type=participant2_data.get("type", "player"),
                name=participant2_data.get("name", f"Entity_{participant2_data['id']}")
            )

            conversation_id = str(uuid.uuid4())
            now = datetime.now()
            
            conversation = Conversation(
                id=conversation_id,
                type=type,
                participants={
                    participant1.id: participant1,
                    participant2.id: participant2
                },
                messages=[],
                created_at=now,
                last_update=now,
                metadata={}
            )
            
            # Store conversation
            self.conversations[conversation_id] = conversation
            
            # Update participant indexes
            for p_id in [participant1.id, participant2.id]:
                if p_id not in self.participant_conversations:
                    self.participant_conversations[p_id] = []
                self.participant_conversations[p_id].append(conversation_id)
            
            # Update metrics
            self.metrics.total_conversations += 1
            self.metrics.active_conversations += 1
                
            logger.info(f"Created conversation {conversation_id} between {participant1.name} and {participant2.name}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None

    def add_message(self, conversation_id: str, sender_id: str, content: str) -> bool:
        """Add a message to a conversation"""
        try:
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                return False
                
            message = Message(
                sender_id=sender_id,
                content=content,
                timestamp=datetime.now()
            )
            
            conversation.messages.append(message)
            conversation.last_update = datetime.now()
            
            # Update metrics
            self.metrics.total_messages += 1
            
            return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False

    def end_conversation(self, conversation_id: str) -> bool:
        """End and clean up a conversation"""
        try:
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                return False
                
            # Update metrics
            self.metrics.active_conversations -= 1
            self.metrics.completed_conversations += 1
            
            # Calculate response time metrics
            if len(conversation.messages) > 1:
                total_time = (conversation.last_update - conversation.created_at).total_seconds()
                avg_time = total_time / len(conversation.messages)
                self._update_average_response_time(avg_time)
            
            # Remove from participant tracking
            for participant_id in conversation.participants:
                if participant_id in self.participant_conversations:
                    self.participant_conversations[participant_id].remove(conversation_id)
                    
            # Remove conversation
            del self.conversations[conversation_id]
            return True
            
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return False

    def _update_average_response_time(self, response_time: float):
        """Update average response time metric"""
        current = self.metrics.average_response_time
        total = self.metrics.total_messages
        if total > 0:
            self.metrics.average_response_time = (current * (total - 1) + response_time) / total
        else:
            self.metrics.average_response_time = response_time

    def get_history(self, conversation_id: str, limit: Optional[int] = None) -> List[str]:
        """Get conversation history as a list of messages"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return []
            
        messages = [msg.content for msg in conversation.messages]
        if limit:
            messages = messages[-limit:]
            
        return messages

    def get_conversation_context(self, conversation_id: str) -> Dict:
        """Get full conversation context"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {}
            
        return {
            "type": conversation.type,
            "participants": {
                pid: participant.model_dump() 
                for pid, participant in conversation.participants.items()
            },
            "created_at": conversation.created_at.isoformat(),
            "last_update": conversation.last_update.isoformat(),
            "message_count": len(conversation.messages),
            "metadata": conversation.metadata
        }

    def get_active_conversations(self, participant_id: str) -> List[str]:
        """Get all active conversations for a participant"""
        return self.participant_conversations.get(participant_id, [])

    def cleanup_expired(self) -> int:
        """Remove expired conversations"""
        now = datetime.now()
        expired = []
        
        for conv_id, conv in self.conversations.items():
            if now - conv.last_update > self.expiry_time:
                expired.append(conv_id)
                
        for conv_id in expired:
            self.end_conversation(conv_id)
            
        return len(expired)
```
