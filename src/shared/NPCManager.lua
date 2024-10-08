-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")

local NPCManagerV3 = {}
NPCManagerV3.__index = NPCManagerV3

local API_URL = "https://www.ella-ai-care.com/robloxgpt/v3"
local RESPONSE_COOLDOWN = 1
local FOLLOW_DURATION = 60 -- Follow for 60 seconds by default
local MIN_FOLLOW_DISTANCE = 5 -- Minimum distance to keep from the player
local MEMORY_EXPIRATION = 3600 -- Remember players for 1 hour (in seconds)
local VISION_RANGE = 50 -- Range in studs for NPC vision

local NPCChatEvent = ReplicatedStorage:FindFirstChild("NPCChatEvent") or Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

function NPCManagerV3.new()
	local self = setmetatable({}, NPCManagerV3)
	self.npcs = {}
	self:loadNPCDatabase()
	return self
end

function NPCManagerV3:loadNPCDatabase()
	local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
	for _, npcData in ipairs(npcDatabase.npcs) do
		self:createNPC(npcData)
	end
end

function NPCManagerV3:createNPC(npcData)
	if not workspace:FindFirstChild("NPCs") then
		Instance.new("Folder", workspace).Name = "NPCs"
	end

	local model = ServerStorage.NPCModels:FindFirstChild(npcData.model)
	if not model then
		warn("Model not found for NPC: " .. npcData.displayName)
		return
	end

	local npcModel = model:Clone()
	npcModel.Parent = workspace.NPCs

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
	}

	self:setupClickDetector(npc)
	self.npcs[npc.id] = npc
	print("V3 NPC created: " .. npc.displayName)
end

function NPCManagerV3:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius
	clickDetector.Parent = npc.model.PrimaryPart

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManagerV3:updateNPCVision(npc)
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
			end
		end
	end

	-- Detect objects (you'll need to define what objects are detectable)
	local detectableObjects = workspace:FindPartsInRegion3(
		Region3.new(
			npcPosition - Vector3.new(VISION_RANGE, VISION_RANGE, VISION_RANGE),
			npcPosition + Vector3.new(VISION_RANGE, VISION_RANGE, VISION_RANGE)
		),
		nil,
		100
	)

	for _, object in ipairs(detectableObjects) do
		if object.Parent and object.Parent ~= npc.model and object.Parent:FindFirstChild("Detectable") then
			local distance = (object.Position - npcPosition).Magnitude
			table.insert(npc.visibleEntities, {
				type = "object",
				name = object.Parent.Name,
				distance = distance,
			})
		end
	end
end

function NPCManagerV3:handleNPCInteraction(npc, player, message)
	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		return
	end

	npc.isInteracting = true
	npc.interactingPlayer = player

	local response = self:getResponseFromAI(npc, player, message)
	if response then
		npc.lastResponseTime = currentTime
		self:processAIResponse(npc, player, response)
	end
end

function NPCManagerV3:getResponseFromAI(npc, player, message)
	local perceptionData = self:getPerceptionData(npc)
	local playerContext = self:getPlayerContext(player)

	local data = {
		message = message,
		player_id = tostring(player.UserId),
		npc_id = npc.id,
		npc_name = npc.displayName,
		system_prompt = npc.system_prompt,
		perception = perceptionData,
		context = playerContext,
	}

	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
	end)

	if success then
		local parsed = HttpService:JSONDecode(response)
		return parsed
	end
	return nil
end

function NPCManagerV3:processAIResponse(npc, player, response)
	if response.message then
		self:displayMessage(npc, response.message, player)
	end

	if response.action then
		self:executeAction(npc, player, response.action)
	end

	if response.internal_state then
		self:updateInternalState(npc, response.internal_state)
	end
end

function NPCManagerV3:displayMessage(npc, message, player)
	local ChatService = game:GetService("Chat")
	ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)
	NPCChatEvent:FireClient(player, npc.displayName, message)
end

function NPCManagerV3:executeAction(npc, player, action)
	if action.type == "emote" and action.data and action.data.emote then
		self:playEmote(npc, action.data.emote)
	elseif action.type == "move" and action.data and action.data.position then
		self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
	elseif action.type == "follow" then
		self:startFollowing(npc, player)
	elseif action.type == "unfollow" then
		self:stopFollowing(npc)
	end
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

function NPCManagerV3:startFollowing(npc, player)
	npc.isFollowing = true
	npc.followTarget = player
	npc.followStartTime = tick()
end

function NPCManagerV3:stopFollowing(npc)
	npc.isFollowing = false
	npc.followTarget = nil
end

function NPCManagerV3:updateNPCState(npc)
	self:updateNPCVision(npc)

	if npc.isInteracting then
		if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
			npc.isInteracting = false
			npc.interactingPlayer = nil
		end
	end

	if npc.isFollowing then
		self:updateFollowing(npc)
	elseif not npc.isInteracting and not npc.isMoving then
		self:randomWalk(npc)
	end
end

function NPCManagerV3:isPlayerInRange(npc, player)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if playerPosition and npc.model.PrimaryPart then
		local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
		return distance <= npc.responseRadius
	end
	return false
end

function NPCManagerV3:updateFollowing(npc)
	if not npc.followTarget or not npc.followTarget.Character then
		self:stopFollowing(npc)
		return
	end

	local currentTime = tick()
	if currentTime - npc.followStartTime > FOLLOW_DURATION then
		self:stopFollowing(npc)
		return
	end

	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		local targetPosition = npc.followTarget.Character.HumanoidRootPart.Position
		local npcPosition = npc.model.PrimaryPart.Position
		local direction = (targetPosition - npcPosition).Unit
		local distanceToTarget = (targetPosition - npcPosition).Magnitude

		if distanceToTarget > MIN_FOLLOW_DISTANCE + 1 then
			local newPosition = npcPosition + direction * (distanceToTarget - MIN_FOLLOW_DISTANCE)
			humanoid:MoveTo(newPosition)
		else
			humanoid:Move(Vector3.new(0, 0, 0)) -- Stop moving if close enough
		end
	end
end

function NPCManagerV3:randomWalk(npc)
	if npc.isInteracting or npc.isMoving then
		return
	end

	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		local currentPosition = npc.model.PrimaryPart.Position
		local randomOffset = Vector3.new(math.random(-5, 5), 0, math.random(-5, 5))
		local targetPosition = currentPosition + randomOffset

		npc.isMoving = true
		humanoid:MoveTo(targetPosition)

		humanoid.MoveToFinished:Wait()
		npc.isMoving = false
	end
end

function NPCManagerV3:getPerceptionData(npc)
	return {
		visible_objects = self:getVisibleObjects(npc),
		visible_players = self:getVisiblePlayers(npc),
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

return NPCManagerV3
