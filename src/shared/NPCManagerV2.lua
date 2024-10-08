-- NPCManagerV2.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ChatService = game:GetService("Chat")
local Players = game:GetService("Players")

local NPCManagerV2 = {}
NPCManagerV2.__index = NPCManagerV2

local API_URL = "https://www.ella-ai-care.com/robloxgpt/v2"
local RESPONSE_COOLDOWN = 1
local FOLLOW_DURATION = 60 -- Follow for 60 seconds by default
local MIN_FOLLOW_DISTANCE = 5 -- Minimum distance to keep from the player
local MEMORY_EXPIRATION = 3600 -- Remember players for 1 hour (in seconds)
local VISION_RANGE = 50 -- Range in studs for NPC vision
local GREETING_COOLDOWN = 300 -- 5 minutes cooldown between greetings

local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

function NPCManagerV2.new()
	local self = setmetatable({}, NPCManagerV2)
	self.npcs = {}
	self:loadNPCDatabase()
	return self
end

function NPCManagerV2:loadNPCDatabase()
	local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV2"))
	for _, npcData in ipairs(npcDatabase.npcs) do
		self:createNPC(npcData)
	end
end

function NPCManagerV2:createNPC(npcData)
	local model = ServerStorage.NPCModels:FindFirstChild(npcData.model)
	if not model then
		warn("Model not found for NPC: " .. npcData.displayName)
		return
	end

	local npcModel = model:Clone()
	npcModel.Parent = workspace.NPCs

	local primaryPart = npcModel:FindFirstChild("HumanoidRootPart") or npcModel:FindFirstChildWhichIsA("BasePart")
	if primaryPart then
		npcModel.PrimaryPart = primaryPart
		npcModel:SetPrimaryPartCFrame(CFrame.new(unpack(npcData.spawnPosition)))
	else
		warn("No suitable part found to set as PrimaryPart for " .. npcData.displayName)
		return
	end

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
		greetedPlayers = {},
		waypoints = npcData.waypoints or {},
		currentWaypointIndex = 1,
		patrolling = npcData.patrolling or false,
		memory = {}, -- Stores player interactions
		objectMemory = {}, -- Stores object interactions
		visibleEntities = {}, -- Stores currently visible entities
		lastGreetingTime = {}, -- Stores last greeting time for each player
	}

	self:setupClickDetector(npc)
	self.npcs[npc.id] = npc
	print("V2 NPC created: " .. npc.displayName)
end

function NPCManagerV2:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius
	clickDetector.Parent = npc.model.PrimaryPart

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManagerV2:displayMessage(npc, message, player)
	ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)
	NPCChatEvent:FireClient(player, npc.displayName, message) -- Use the same event as v1 NPCs
end

function NPCManagerV2:stopNPCMovement(npc)
	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		humanoid:MoveTo(npc.model.PrimaryPart.Position)
	end
	npc.isMoving = false
end

function NPCManagerV2:updateNPCVision(npc)
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

function NPCManagerV2:updateMemory(npc, player, message, isGreeting)
	local currentTime = tick()
	local userId = player.UserId

	if not npc.memory[userId] then
		npc.memory[userId] = {}
	end

	table.insert(npc.memory[userId], {
		timestamp = currentTime,
		message = message,
		isGreeting = isGreeting,
	})

	-- Limit memory to last 10 interactions
	if #npc.memory[userId] > 10 then
		table.remove(npc.memory[userId], 1)
	end
end

function NPCManagerV2:getRecentMemory(npc, player)
	local memory = npc.memory[player.UserId]
	if memory then
		local recentMemories = {}
		local currentTime = tick()
		for i = #memory, 1, -1 do
			if currentTime - memory[i].timestamp <= MEMORY_EXPIRATION then
				table.insert(recentMemories, memory[i])
			else
				break
			end
		end
		return recentMemories
	end
	return nil
end

function NPCManagerV2:getMemory(npc, player)
	local memory = npc.memory[player.UserId]
	if memory and (tick() - memory.lastInteraction) <= MEMORY_EXPIRATION then
		return memory
	end
	return nil
end

function NPCManagerV2:isPlayerInRange(npc, player)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if playerPosition and npc.model.PrimaryPart then
		local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
		return distance <= npc.responseRadius
	end
	return false
end

function NPCManagerV2:patrolToNextWaypoint(npc)
	if npc.isInteracting then
		return
	end

	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid and not npc.isMoving then
		local nextWaypoint = npc.waypoints[npc.currentWaypointIndex]

		npc.isMoving = true
		humanoid:MoveTo(nextWaypoint)

		humanoid.MoveToFinished:Wait()
		npc.isMoving = false

		-- Move to the next waypoint
		npc.currentWaypointIndex = (npc.currentWaypointIndex % #npc.waypoints) + 1
	end
end

function NPCManagerV2:randomWalk(npc)
	if npc.isInteracting then
		return
	end -- Don't walk if interacting

	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid and not npc.isMoving then
		local currentPosition = npc.model.PrimaryPart.Position
		local randomOffset = Vector3.new(math.random(-5, 5), 0, math.random(-5, 5))
		local targetPosition = currentPosition + randomOffset

		npc.isMoving = true
		humanoid:MoveTo(targetPosition)

		humanoid.MoveToFinished:Wait()
		npc.isMoving = false
	end
end

-- NPCManagerV2.lua
-- ... (previous code remains the same)

function NPCManagerV2:getResponseFromAI(npc, player, message, isGreeting)
	local recentMemories = self:getRecentMemory(npc, player) or {}
	local visibleEntities = npc.visibleEntities

	local data = {
		message = message,
		player_id = tostring(player.UserId),
		player_name = player.Name,
		npc_id = npc.id,
		npc_name = npc.displayName,
		system_prompt = npc.system_prompt,
		is_greeting = isGreeting,
		recent_memories = recentMemories,
		visible_entities = visibleEntities,
		current_time = os.date("%Y-%m-%d %H:%M:%S"),
		limit = 200,
	}

	if isGreeting then
		data.message = "Generate a greeting for "
			.. player.Name
			.. " based on recent memories and visible entities. If no recent memories, use a standard greeting."
	end

	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
	end)

	if success then
		local parsed = HttpService:JSONDecode(response)
		if parsed and parsed.message then
			return parsed.message
		end
	end
	return nil
end

function NPCManagerV2:handleProximityInteraction(npc, player)
	local currentTime = tick()
	local userId = player.UserId

	if not npc.lastGreetingTime[userId] then
		npc.lastGreetingTime[userId] = 0 -- Initialize if it doesn't exist
	end

	if (currentTime - npc.lastGreetingTime[userId]) > GREETING_COOLDOWN then
		npc.isInteracting = true
		npc.interactingPlayer = player
		self:stopNPCMovement(npc)

		local greeting = self:getResponseFromAI(npc, player, "", true)
		if greeting then
			self:displayMessage(npc, greeting, player)
			npc.lastGreetingTime[userId] = currentTime
			self:updateMemory(npc, player, greeting, true)
		end

		-- Keep the NPC in interaction mode for a short while
		delay(5, function()
			if npc.interactingPlayer == player then
				npc.isInteracting = false
				npc.interactingPlayer = nil
			end
		end)
	end
end

function NPCManagerV2:updateNPCState(npc)
	self:updateNPCVision(npc) -- Update vision before other actions

	if npc.isInteracting then
		if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
			npc.isInteracting = false
			npc.interactingPlayer = nil
		end
	end

	if npc.isFollowing then
		self:updateFollowing(npc)
	elseif not npc.isInteracting and not npc.isMoving then
		if npc.patrolling and #npc.waypoints > 0 then
			self:patrolToNextWaypoint(npc)
		else
			self:randomWalk(npc)
		end
	end
end

function NPCManagerV2:handleNPCInteraction(npc, player, message)
	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		return
	end

	npc.isInteracting = true
	npc.interactingPlayer = player

	-- Check for commands
	local command = self:checkForCommand(message)
	if command then
		self:executeCommand(npc, player, command)
	else
		-- Normal interaction
		local response = self:getResponseFromAI(npc, player, message, false)
		if response then
			self:displayMessage(npc, response, player)
			npc.lastResponseTime = currentTime
		end
	end

	-- Update memory
	self:updateMemory(npc, player, message, false)
end

function NPCManagerV2:checkForCommand(message)
	local lowerMessage = message:lower()
	if lowerMessage:match("^follow me") or lowerMessage:match("^follow") then
		return "follow"
	elseif lowerMessage:match("^stop following") or lowerMessage:match("^unfollow") or lowerMessage:match("^stop") then
		return "unfollow"
	end
	return nil
end

function NPCManagerV2:executeCommand(npc, player, command)
	if command == "follow" then
		self:startFollowing(npc, player)
	elseif command == "unfollow" then
		self:stopFollowing(npc)
	end
end

function NPCManagerV2:startFollowing(npc, player)
	npc.isFollowing = true
	npc.followTarget = player
	npc.followStartTime = tick()
	self:displayMessage(npc, "Certainly! I'll follow you for a while.", player)
	print("NPC " .. npc.displayName .. " started following " .. player.Name)
end

function NPCManagerV2:stopFollowing(npc)
	npc.isFollowing = false
	npc.followTarget = nil
	if npc.interactingPlayer then
		self:displayMessage(npc, "Alright, I'll stop following you now.", npc.interactingPlayer)
	end
	print("NPC " .. npc.displayName .. " stopped following")
end

function NPCManagerV2:updateFollowing(npc)
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

return NPCManagerV2
