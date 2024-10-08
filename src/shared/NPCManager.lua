-- NPCManager.lua (v1)
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ChatService = game:GetService("Chat")

local NPCManager = {}
NPCManager.__index = NPCManager

local API_URL = "https://www.ella-ai-care.com/robloxgpt"
local RESPONSE_COOLDOWN = 1

local NPCChatEvent = Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

function NPCManager.new()
	local self = setmetatable({}, NPCManager)
	self.npcs = {}
	self:loadNPCDatabase()
	return self
end

function NPCManager:loadNPCDatabase()
	local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabase"))
	for _, npcData in ipairs(npcDatabase.npcs) do
		self:createNPC(npcData)
	end
end

function NPCManager:createNPC(npcData)
	local model = ServerStorage.NPCModels:FindFirstChild(npcData.model)
	if not model then
		return
	end

	local npcModel = model:Clone()
	npcModel.Parent = workspace.NPCs

	local primaryPart = npcModel:FindFirstChild("HumanoidRootPart") or npcModel:FindFirstChildWhichIsA("BasePart")
	if primaryPart then
		npcModel.PrimaryPart = primaryPart
		npcModel:SetPrimaryPartCFrame(CFrame.new(unpack(npcData.spawnPosition)))
	else
		return
	end

	local npc = {
		model = npcModel,
		id = npcData.id,
		displayName = npcData.displayName,
		responseRadius = npcData.responseRadius,
		lastResponseTime = 0,
		isMoving = false,
		isInteracting = false,
		greetedPlayers = {},
	}

	self:setupClickDetector(npc)
	self.npcs[npc.id] = npc
end

function NPCManager:setupClickDetector(npc)
	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius
	clickDetector.Parent = npc.model.PrimaryPart

	clickDetector.MouseClick:Connect(function(player)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManager:getResponseFromAI(npc, message, player)
	local data = {
		message = message,
		player_id = tostring(player.UserId),
		npc_id = npc.id,
		npc_name = npc.displayName,
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

function NPCManager:displayMessage(npc, message, player)
	ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)
	NPCChatEvent:FireClient(player, npc.displayName, message)
end

function NPCManager:stopNPCMovement(npc)
	local humanoid = npc.model:FindFirstChild("Humanoid")
	if humanoid then
		humanoid:MoveTo(npc.model.PrimaryPart.Position)
	end
	npc.isMoving = false
end

function NPCManager:handleNPCInteraction(npc, player, message)
	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		return
	end

	npc.isInteracting = true
	npc.interactingPlayer = player
	self:stopNPCMovement(npc)

	local response = self:getResponseFromAI(npc, message, player)
	if response then
		self:displayMessage(npc, response, player)
		npc.lastResponseTime = currentTime
	end

	-- Don't reset isInteracting here, it will be reset in updateNPCState
end

function NPCManager:handleProximityInteraction(npc, player)
	if not npc.greetedPlayers[player.UserId] then
		self:handleNPCInteraction(npc, player, "Hello")
		npc.greetedPlayers[player.UserId] = true
	end
end

function NPCManager:isPlayerInRange(npc, player)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if playerPosition and npc.model.PrimaryPart then
		local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
		return distance <= npc.responseRadius
	end
	return false
end

function NPCManager:updateNPCState(npc)
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

function NPCManager:randomWalk(npc)
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

return NPCManager
