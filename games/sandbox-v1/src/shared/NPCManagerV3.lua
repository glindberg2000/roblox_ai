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

