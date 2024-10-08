-- NPCManagerV2.lua
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ChatService = game:GetService("Chat")

local NPCManagerV2 = {}
NPCManagerV2.__index = NPCManagerV2

local API_URL = "https://www.ella-ai-care.com/robloxgpt/v2"
local RESPONSE_COOLDOWN = 1

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
		greetedPlayers = {},
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

function NPCManagerV2:getResponseFromAI(npc, player, message)
	local data = {
		message = message,
		player_id = tostring(player.UserId),
		npc_id = npc.id,
		npc_name = npc.displayName,
		system_prompt = npc.system_prompt,
		limit = 200,
	}

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

function NPCManagerV2:handleNPCInteraction(npc, player, message)
	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		return
	end

	npc.isInteracting = true
	npc.interactingPlayer = player
	self:stopNPCMovement(npc)

	local response = self:getResponseFromAI(npc, player, message)
	if response then
		self:displayMessage(npc, response, player)
		npc.lastResponseTime = currentTime
	end

	-- Don't reset isInteracting here, it will be reset in updateNPCState
end

function NPCManagerV2:handleProximityInteraction(npc, player)
	if not npc.greetedPlayers[player.UserId] then
		self:handleNPCInteraction(npc, player, "Hello")
		npc.greetedPlayers[player.UserId] = true
	end
end

function NPCManagerV2:isPlayerInRange(npc, player)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if playerPosition and npc.model.PrimaryPart then
		local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
		return distance <= npc.responseRadius
	end
	return false
end

function NPCManagerV2:updateNPCState(npc)
	if npc.isInteracting then
		if npc.interactingPlayer and not self:isPlayerInRange(npc, npc.interactingPlayer) then
			npc.isInteracting = false
			npc.interactingPlayer = nil
			npc.greetedPlayers = {} -- Reset greeted players when interaction ends
		end
	end

	if not npc.isInteracting and not npc.isMoving then
		self:randomWalk(npc)
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

return NPCManagerV2
