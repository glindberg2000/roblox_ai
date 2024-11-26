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
    else
        Logger = {
            log = function(_, category, message)
                print(string.format("[%s] %s", category, message))
            end
        }
    end
end

initializeLogger()

local NPCManagerV3 = {}
NPCManagerV3.__index = NPCManagerV3

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

function NPCManagerV3.new()
    local self = setmetatable({}, NPCManagerV3)
    self.npcs = {}
    self.responseCache = {}
    self.interactionController = InteractionController.new()
    Logger:log("SYSTEM", "Initializing NPCManagerV3")
    self:loadNPCDatabase()
    return self
end

function NPCManagerV3:loadNPCDatabase()
    local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
    Logger:log("SYSTEM", string.format("Loading NPCs from database: %d NPCs found", #npcDatabase.npcs))
    
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
	return count
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius

	-- Try to parent to HumanoidRootPart, if not available, use any BasePart
	local parent = npc.model:FindFirstChild("HumanoidRootPart") or npc.model:FindFirstChildWhichIsA("BasePart")

	if parent then
		clickDetector.Parent = parent
	else
		warn("Could not find suitable part for ClickDetector on " .. npc.displayName)
		return
	end

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManagerV3:handleNPCInteraction(npc, player, message)
    Logger:log("INTERACTION", string.format("Handling interaction: %s with %s - Message: %s",
        npc.displayName,
        player.Name,
        message
    ))

    if self.interactionController:isInGroupInteraction(player) then
        Logger:log("INTERACTION", string.format("Group interaction detected for %s", player.Name))
        self:handleGroupInteraction(npc, player, message)
        return
    end

    if not self.interactionController:canInteract(player) then
        local interactingNPC = self.interactionController:getInteractingNPC(player)
        if interactingNPC ~= npc then
            Logger:log("INTERACTION", string.format("Player %s is already interacting with another NPC", player.Name))
            return
        end
    else
        if not self.interactionController:startInteraction(player, npc) then
            Logger:log("ERROR", string.format("Failed to start interaction between %s and %s", npc.displayName, player.Name))
            return
        end
    end

    local currentTime = tick()
    if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
        Logger:log("INTERACTION", string.format("Interaction cooldown for %s (%.1f seconds remaining)", 
            npc.displayName, 
            RESPONSE_COOLDOWN - (currentTime - npc.lastResponseTime)
        ))
        return
    end

    npc.isInteracting = true
    npc.interactingPlayer = player

    local response = self:getResponseFromAI(npc, player, message)
    if response then
        npc.lastResponseTime = currentTime
        self:processAIResponse(npc, player, response)
    else
        Logger:log("ERROR", string.format("Failed to get AI response for %s", npc.displayName))
        self:endInteraction(npc, player)
    end
end

function NPCManagerV3:handleGroupInteraction(npc, player, message)
	local group = self.interactionController:getGroupParticipants(player)
	local messages = {}
	for _, participant in ipairs(group) do
		table.insert(messages, { player = participant, message = message })
	end
	local response = self:getGroupResponseFromAI(npc, group, messages)
	self:processGroupAIResponse(npc, group, response)
end

-- Function to get the player's description
local function getPlayerDescription(player)
	local playerDescFolder = ReplicatedStorage:FindFirstChild("PlayerDescriptions")
	if playerDescFolder then
		local description = playerDescFolder:FindFirstChild(player.Name)
		if description then
			return description.Value
		end
	end
	return "No description available."
end

-- Modified getResponseFromAI to include player description
function NPCManagerV3:getResponseFromAI(npc, player, message)
	local interactionState = self.interactionController:getInteractionState(player)
	local playerMemory = npc.shortTermMemory[player.UserId] or {}

	local cacheKey = self:getCacheKey(npc, player, message)
	if self.responseCache[cacheKey] then
		return self.responseCache[cacheKey]
	end

	-- Get the player's avatar description
	local playerDescription = getPlayerDescription(player)

	-- Update the prompt to include the player's description
	local data = {
		message = message,
		player_id = tostring(player.UserId),
		npc_id = npc.id,
		npc_name = npc.displayName,
		system_prompt = npc.system_prompt .. "\n\nPlayer Description: " .. playerDescription,
		perception = self:getPerceptionData(npc),
		context = self:getPlayerContext(player),
		interaction_state = interactionState,
		memory = playerMemory,
		limit = 200,
	}

	-- Make the API call
	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
	end)

	if success then
		self:log("Raw API response: " .. response)
		local parsed = HttpService:JSONDecode(response)
		self:log("Parsed API response: " .. HttpService:JSONEncode(parsed))
		if parsed and parsed.message then
			self:log("Parsed API response: " .. HttpService:JSONEncode(parsed))
			self.responseCache[cacheKey] = parsed
			npc.shortTermMemory[player.UserId] = {
				lastInteractionTime = tick(),
				recentTopics = parsed.topics_discussed or {},
			}
			return parsed
		else
			self:log("Invalid response format received from API")
		end
	else
		self:log("Failed to get AI response: " .. tostring(response))
	end

	return nil
end

function NPCManagerV3:log(message)
	print("[NPCManagerV3] " .. os.date("%Y-%m-%d %H:%M:%S") .. ": " .. message)
end

function NPCManagerV3:processAIResponse(npc, player, response)
    Logger:log("RESPONSE", string.format("Processing AI response for %s: %s",
        npc.displayName,
        HttpService:JSONEncode(response)
    ))

    if response.action and response.action.type == "stop_interacting" then
        Logger:log("ACTION", string.format("Stopping interaction for %s as per AI response", npc.displayName))
        self:endInteraction(npc, player)
        return
    end

    if response.message then
        Logger:log("CHAT", string.format("Displaying message from %s: %s",
            npc.displayName,
            response.message
        ))
        self:displayMessage(npc, response.message, player)
    end

    if response.action then
        Logger:log("ACTION", string.format("Executing action for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.action)
        ))
        self:executeAction(npc, player, response.action)
    end

    if response.internal_state then
        Logger:log("STATE", string.format("Updating internal state for %s: %s",
            npc.displayName,
            HttpService:JSONEncode(response.internal_state)
        ))
        self:updateInternalState(npc, response.internal_state)
    end
end

function NPCManagerV3:endInteraction(npc, player)
	npc.isInteracting = false
	npc.interactingPlayer = nil
	self.interactionController:endInteraction(player)
	-- Remove this line to prevent the message from appearing in the chat
	-- NPCChatEvent:FireClient(player, npc.displayName, "The interaction has ended.")
	self:log("Interaction ended between " .. npc.displayName .. " and " .. player.Name)
end

function NPCManagerV3:getCacheKey(npc, player, message)
	local context = {
		npcId = npc.id,
		playerId = player.UserId,
		message = message,
		memory = npc.shortTermMemory[player.UserId],
	}
	return HttpService:JSONEncode(context)
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
    Logger:log("VISION", string.format("Updating vision for %s", npc.displayName))
    npc.visibleEntities = {}
    local npcPosition = npc.model.PrimaryPart.Position

    -- Detect players
    for _, player in ipairs(Players:GetPlayers()) do
        if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local distance = (player.Character.HumanoidRootPart.Position - npcPosition).Magnitude
            if distance <= VISION_RANGE then
                table.insert(npc.visibleEntities, {
                    type = "player",
                    name = player.Name,
                    distance = distance,
                })
                Logger:log("VISION", string.format("%s sees player: %s at distance: %.2f",
                    npc.displayName,
                    player.Name,
                    distance
                ))
            end
        end
    end

    -- Detect objects and fetch descriptions from AssetDatabase
    local detectedObjects = {}
    for _, object in ipairs(workspace:GetChildren()) do
        if object:IsA("Model") and object ~= npc.model then
            local primaryPart = object.PrimaryPart or object:FindFirstChildWhichIsA("BasePart")
            if primaryPart then
                local distance = (primaryPart.Position - npcPosition).Magnitude
                if distance <= VISION_RANGE then
                    -- Fetch asset data from the AssetDatabase
                    local assetData = getAssetData(object.Name)
                    if assetData then
                        local key = object.Name .. "_" .. assetData.assetId
                        if not detectedObjects[key] then
                            detectedObjects[key] = true
                            table.insert(npc.visibleEntities, {
                                type = "object",
                                name = assetData.name,
                                objectType = assetData.description,
                                distance = distance,
                                imageUrl = assetData.imageUrl,
                            })
                            Logger:log("VISION", string.format("%s sees object: %s (Description: %s) at distance: %.2f",
                                npc.displayName,
                                assetData.name,
                                assetData.description,
                                distance
                            ))
                        end
                    else
                        -- If asset data is not found, fall back to default behavior
                        local key = object.Name .. "_Unknown"
                        if not detectedObjects[key] then
                            detectedObjects[key] = true
                            table.insert(npc.visibleEntities, {
                                type = "object",
                                name = object.Name,
                                objectType = "Unknown",
                                distance = distance,
                            })
                            Logger:log("VISION", string.format("%s sees object: %s (Type: Unknown) at distance: %.2f",
                                npc.displayName,
                                object.Name,
                                distance
                            ))
                        end
                    end
                end
            end
        end
    end

    Logger:log("VISION", string.format("%s vision update complete. Visible entities: %d",
        npc.displayName,
        #npc.visibleEntities
    ))
end

function NPCManagerV3:displayMessage(npc, message, player)
    Logger:log("CHAT", string.format("NPC %s sending message to %s: %s", 
        npc.displayName,
        player and player.Name or "all players",
        message
    ))

    -- Display chat bubble
    ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)

    -- Fire event to display in chat box
    if player then
        NPCChatEvent:FireClient(player, npc.displayName, message)
    else
        NPCChatEvent:FireAllClients(npc.displayName, message)
    end
end

function NPCManagerV3:executeAction(npc, player, action)
	self:log("Executing action: " .. action.type .. " for " .. npc.displayName)
	if action.type == "follow" then
		self:log("Starting to follow player: " .. player.Name)
		self:startFollowing(npc, player)
	elseif action.type == "unfollow" or (action.type == "none" and npc.isFollowing) then
		self:log("Stopping following player: " .. player.Name)
		self:stopFollowing(npc)
	elseif action.type == "emote" and action.data and action.data.emote then
		self:log("Playing emote: " .. action.data.emote)
		self:playEmote(npc, action.data.emote)
	elseif action.type == "move" and action.data and action.data.position then
		self:log("Moving to position: " .. tostring(action.data.position))
		self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
	else
		self:log("Unknown action type: " .. action.type)
	end
end

function NPCManagerV3:startFollowing(npc, player)
	self:log(npc.displayName .. " starting to follow " .. player.Name)
	npc.isFollowing = true
	npc.followTarget = player
	npc.followStartTime = tick()

	-- Play walk animation
	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		AnimationManager:playAnimation(humanoid, "walk")
	end
	
	self:log(
		"Follow state set for "
			.. npc.displayName
			.. ": isFollowing="
			.. tostring(npc.isFollowing)
			.. ", followTarget="
			.. player.Name
	)
end

function NPCManagerV3:updateInternalState(npc, internalState)
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
		else
			warn("Animation not found: " .. emoteName)
		end
	end
end

function NPCManagerV3:moveNPC(npc, targetPosition)
	local Humanoid = npc.model:FindFirstChildOfClass("Humanoid")
	if Humanoid then
		Humanoid:MoveTo(targetPosition)
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

	self:log(npc.displayName .. " stopped following and movement halted")
end

function NPCManagerV3:updateNPCState(npc)
	self:updateNPCVision(npc)

	local humanoid = npc.model:FindFirstChild("Humanoid")

	if npc.isFollowing then
		self:updateFollowing(npc)
		if humanoid then
			AnimationManager:playAnimation(humanoid, "walk")
		end
	elseif npc.isInteracting then
		if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
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
		return distance <= npc.responseRadius
	end
	return false
end

function NPCManagerV3:updateFollowing(npc)
	if not npc.isFollowing then
		return -- Exit early if not following
	end
	if not npc.followTarget or not npc.followTarget.Character then
		self:log(npc.displayName .. ": Follow target lost, stopping follow")
		self:stopFollowing(npc)
		return
	end

	local targetPosition = npc.followTarget.Character:FindFirstChild("HumanoidRootPart")
	if not targetPosition then
		self:log(npc.displayName .. ": Cannot find target position, stopping follow")
		self:stopFollowing(npc)
		return
	end

	local npcPosition = npc.model.PrimaryPart.Position
	local direction = (targetPosition.Position - npcPosition).Unit
	local distance = (targetPosition.Position - npcPosition).Magnitude

	if distance > MIN_FOLLOW_DISTANCE + 1 then
		local newPosition = npcPosition + direction * (distance - MIN_FOLLOW_DISTANCE)
		self:log(npc.displayName .. " moving to " .. tostring(newPosition))
		npc.model.Humanoid:MoveTo(newPosition)
	else
		self:log(npc.displayName .. " is close enough to target")
		npc.model.Humanoid:Move(Vector3.new(0, 0, 0)) -- Stop moving
	end

	-- Check if follow duration has expired
	if tick() - npc.followStartTime > FOLLOW_DURATION then
		self:log(npc.displayName .. ": Follow duration expired, stopping follow")
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
	return {
		visible_objects = visibleObjects,
		visible_players = visiblePlayers,
		memory = self:getRecentMemories(npc),
	}
end

function NPCManagerV3:getPlayerContext(player)
	return {
		player_name = player.Name,
		is_new_conversation = self:isNewConversation(player),
		time_since_last_interaction = self:getTimeSinceLastInteraction(player),
		nearby_players = self:getNearbyPlayerNames(player),
		npc_location = self:getNPCLocation(player),
	}
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
		self:log("Testing follow functionality for NPC: " .. npc.displayName)
		self:startFollowing(npc, player)
		wait(5) -- Wait for 5 seconds
		self:updateFollowing(npc)
		wait(5) -- Wait another 5 seconds
		self:stopFollowing(npc)
		self:log("Follow test completed for NPC: " .. npc.displayName)
	else
		self:log("Failed to find NPC or player for follow test")
	end
end

function NPCManagerV3:testFollowCommand(npcId, playerId)
	local npc = self.npcs[npcId]
	local player = game.Players:GetPlayerByUserId(playerId)
	if npc and player then
		self:log("Testing follow command for " .. npc.displayName)
		self:startFollowing(npc, player)
	else
		self:log("Failed to find NPC or player for follow test")
	end
end

function NPCManagerV3:getInteractionClusters(player)
	local clusters = {}
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not playerPosition then
		return clusters
	end

	for _, npc in pairs(self.npcs) do
		local distance = (npc.model.PrimaryPart.Position - playerPosition.Position).Magnitude
		if distance <= npc.responseRadius then
			local addedToCluster = false
			for _, cluster in ipairs(clusters) do
				if (cluster.center - npc.model.PrimaryPart.Position).Magnitude < 10 then -- Adjust this threshold as needed
					table.insert(cluster.npcs, npc)
					addedToCluster = true
					break
				end
			end
			if not addedToCluster then
				table.insert(clusters, { center = npc.model.PrimaryPart.Position, npcs = { npc } })
			end
		end
	end
	return clusters
end

return NPCManagerV3
