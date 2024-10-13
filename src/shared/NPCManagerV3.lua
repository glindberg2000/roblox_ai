-- NPCManagerV3.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")

local NPCManagerV3 = {}
NPCManagerV3.__index = NPCManagerV3

local API_URL = "https://roblox.ella-ai-care.com/robloxgpt/v3"
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
	print("Loading NPCs from database:", #npcDatabase.npcs)
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
	print("V3 NPC added to table: " .. npc.displayName .. ", Total NPCs: " .. self:getNPCCount())
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
	clickDetector.Parent = npc.model.PrimaryPart

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManagerV3:updateNPCVision(npc)
	print("Updating vision for " .. npc.displayName)
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
				print(npc.displayName .. " sees player: " .. player.Name .. " at distance: " .. distance)
			end
		end
	end

	-- Detect objects
	local detectedObjects = {}
	for _, object in ipairs(workspace:GetChildren()) do
		if object:IsA("Model") and object ~= npc.model then
			local primaryPart = object.PrimaryPart or object:FindFirstChildWhichIsA("BasePart")
			if primaryPart then
				local distance = (primaryPart.Position - npcPosition).Magnitude
				if distance <= VISION_RANGE then
					local objectType = object:GetAttribute("ObjectType") or "Unknown"
					local key = object.Name .. "_" .. objectType
					if not detectedObjects[key] then
						detectedObjects[key] = true
						table.insert(npc.visibleEntities, {
							type = "object",
							name = object.Name,
							objectType = objectType,
							distance = distance,
						})
						print(
							npc.displayName
								.. " sees object: "
								.. object.Name
								.. " (Type: "
								.. objectType
								.. ") at distance: "
								.. distance
						)
					end
				end
			end
		end
	end

	print(npc.displayName .. " vision update complete. Visible entities: " .. #npc.visibleEntities)
end

function NPCManagerV3:handleNPCInteraction(npc, player, message)
	print(npc.displayName .. " handling interaction with " .. player.Name .. ": " .. message)
	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		print(npc.displayName .. " interaction cooldown, skipping")
		return
	end

	npc.isInteracting = true
	npc.interactingPlayer = player

	local response = self:getResponseFromAI(npc, player, message)
	if response then
		npc.lastResponseTime = currentTime
		print(npc.displayName .. " received AI response, processing")
		self:processAIResponse(npc, player, response)
	else
		print(npc.displayName .. " did not receive AI response")
		-- Reset interaction state after a short delay
		delay(5, function()
			if npc.isInteracting then
				npc.isInteracting = false
				npc.interactingPlayer = nil
				print(npc.displayName .. " interaction timeout, resetting state")
			end
		end)
	end
end

function NPCManagerV3:getResponseFromAI(npc, player, message)
	print(npc.displayName .. " requesting AI response for: " .. message)
	local perceptionData = self:getPerceptionData(npc)
	local playerContext = self:getPlayerContext(player)

	local systemPromptAddition = [[
		You can perform the following actions:
		- follow: Start following the player.
		- unfollow: Stop following the player.
		
		Always respond with a message, and include an action when appropriate.
		Ensure the response conforms **strictly** to the following JSON schema:
		{
			"message": "string",
			"action": {
				"type": "string",
				"enum": ["follow", "unfollow", "none"]
			},
			"internal_state": {
				"type": "object"
			}
		}
	]]

	local data = {
		message = message,
		player_id = tostring(player.UserId),
		npc_id = npc.id,
		npc_name = npc.displayName,
		system_prompt = npc.system_prompt .. "\n\n" .. systemPromptAddition,
		perception = perceptionData,
		context = playerContext,
		limit = 200,
	}

	print("Sending data to AI:", HttpService:JSONEncode(data))
	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
	end)

	if success then
		local parsed = HttpService:JSONDecode(response)
		if parsed and parsed.message then
			print(npc.displayName .. " received AI response: " .. tostring(parsed.message))
			return parsed
		else
			print(npc.displayName .. " received invalid response format")
			return nil
		end
	else
		print(npc.displayName .. " failed to get AI response. Error: " .. tostring(response))
		return nil
	end
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
	print("Executing action: " .. action.type)
	if action.type == "emote" and action.data and action.data.emote then
		print("Playing emote: " .. action.data.emote)
		self:playEmote(npc, action.data.emote)
	elseif action.type == "move" and action.data and action.data.position then
		print("Moving to position: " .. tostring(action.data.position))
		self:moveNPC(npc, Vector3.new(action.data.position.x, action.data.position.y, action.data.position.z))
	elseif action.type == "follow" then
		print("Starting to follow player")
		self:startFollowing(npc, player)
	elseif action.type == "unfollow" then
		print("Stopping following player")
		self:stopFollowing(npc)
	else
		print("Unknown action type: " .. action.type)
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
	print("Updating NPC state for: " .. npc.displayName)
	self:updateNPCVision(npc)

	if npc.isInteracting then
		print(npc.displayName .. " is interacting")
		if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
			npc.isInteracting = false
			npc.interactingPlayer = nil
			print(npc.displayName .. " stopped interacting (player out of range)")
		end
	end

	if npc.isFollowing then
		print(npc.displayName .. " is following")
		self:updateFollowing(npc)
	elseif not npc.isInteracting and not npc.isMoving then
		print(npc.displayName .. " is performing random walk")
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
		print(npc.displayName .. " cannot perform random walk (interacting or moving)")
		return
	end

	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		local currentPosition = npc.model.PrimaryPart.Position
		local randomOffset = Vector3.new(math.random(-5, 5), 0, math.random(-5, 5))
		local targetPosition = currentPosition + randomOffset

		npc.isMoving = true
		print(npc.displayName .. " starting random walk to " .. tostring(targetPosition))
		humanoid:MoveTo(targetPosition)

		task.spawn(function()
			task.wait(5) -- Wait for 5 seconds or adjust as needed
			npc.isMoving = false
			print(npc.displayName .. " finished random walk")
		end)
	else
		print(npc.displayName .. " cannot perform random walk (no Humanoid)")
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

return NPCManagerV3
