-- Script Name: NPCManager (v2.3)
-- Script Location: ReplicatedStorage

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local TextChatService = game:GetService("TextChatService")
local ChatService = game:GetService("Chat")

local NPCManager = {}
NPCManager.__index = NPCManager

local API_URL = "https://www.ella-ai-care.com/robloxgpt"
local RESPONSE_RADIUS = 25
local CONVERSATION_TIMEOUT = 60
local RESPONSE_COOLDOWN = 1

local NPCChatEvent = Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

local function log(npcName, message)
	print(string.format("[%s] %s", npcName, message))
end

function NPCManager.new()
	print("NPCManager.new() called")
	local self = setmetatable({}, NPCManager)
	self.npcs = {}
	self:loadNPCDatabase()
	return self
end

function NPCManager:loadNPCDatabase()
	print("Loading NPC Database...")
	local npcDatabaseModule = ReplicatedStorage:WaitForChild("NPCDatabase")
	print("NPCDatabase module found in ReplicatedStorage")
	local npcDatabase = require(npcDatabaseModule)
	print("NPC Database loaded")
	print("Number of NPCs in database:", #npcDatabase.npcs)

	for _, npcData in ipairs(npcDatabase.npcs) do
		print("Creating NPC:", npcData.displayName)
		self:createNPC(npcData)
	end
end

function NPCManager:createNPC(npcData)
	print("Creating NPC:", npcData.displayName)
	local model = ServerStorage.NPCModels:FindFirstChild(npcData.model)
	if not model then
		warn("Model not found for NPC: " .. npcData.displayName)
		return
	end

	local npcModel = model:Clone()
	npcModel.Parent = workspace.NPCs

	-- Find a suitable part to set as PrimaryPart
	local primaryPart = npcModel:FindFirstChild("HumanoidRootPart")
		or npcModel:FindFirstChild("Torso")
		or npcModel:FindFirstChild("UpperTorso")
		or npcModel:FindFirstChildWhichIsA("BasePart")

	if primaryPart then
		npcModel.PrimaryPart = primaryPart
		npcModel:SetPrimaryPartCFrame(CFrame.new(unpack(npcData.spawnPosition)))
		print(npcData.displayName .. " spawned at position: " .. tostring(primaryPart.Position))
	else
		warn("No suitable part found to set as PrimaryPart for " .. npcData.displayName)
		return
	end

	local npc = {
		model = npcModel,
		id = npcData.id,
		displayName = npcData.displayName,
		responseRadius = npcData.responseRadius or RESPONSE_RADIUS,
		backstory = npcData.backstory,
		traits = npcData.traits,
		routines = npcData.routines,
		activeConversations = {},
		lastResponseTime = 0,
	}

	self:setupClickDetector(npc)
	self.npcs[npc.id] = npc

	log(npc.displayName, "NPC created and added to npcs table")
	return npc
end

function NPCManager:setupClickDetector(npc)
	log(npc.displayName, "Setting up ClickDetector")

	local part = self:getInteractionPart(npc.model)
	if not part then
		warn(npc.displayName .. ": Failed to set up ClickDetector - No suitable part found")
		return
	end

	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = npc.responseRadius
	clickDetector.Parent = part

	log(npc.displayName, "ClickDetector parented to " .. part.Name)

	clickDetector.MouseClick:Connect(function(player)
		log(npc.displayName, "Clicked by " .. player.Name)
		self:handleNPCInteraction(npc, player, "Hello")
	end)
end

function NPCManager:getInteractionPart(model)
	return model.PrimaryPart
		or model:FindFirstChild("HumanoidRootPart")
		or model:FindFirstChild("Torso")
		or model:FindFirstChild("UpperTorso")
end

function NPCManager:handleNPCInteraction(npc, player, message)
	log(npc.displayName, "Handling interaction from " .. player.Name .. ": " .. message)

	local currentTime = tick()
	if currentTime - npc.lastResponseTime < RESPONSE_COOLDOWN then
		log(npc.displayName, "Ignoring message due to cooldown")
		return
	end

	local response = self:getResponseFromAI(npc, message, player)
	if response then
		self:displayMessage(npc, response, player)
		self:setActiveConversation(npc, player)
		npc.lastResponseTime = currentTime
	else
		log(npc.displayName, "No response received from AI")
	end
end

function NPCManager:setActiveConversation(npc, player)
	npc.activeConversations[player.UserId] = {
		lastInteractionTime = tick(),
	}
	log(npc.displayName, "Set active conversation with " .. player.Name)
end

function NPCManager:getResponseFromAI(npc, message, player)
	log(npc.displayName, "Getting AI response for: " .. message)

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
			log(npc.displayName, "AI response received: " .. parsed.message)
			return parsed.message
		else
			warn(npc.displayName .. ": Received invalid response from AI")
			return nil
		end
	else
		warn(npc.displayName .. ": Failed to get response from AI: " .. tostring(response))
		return nil
	end
end

function NPCManager:displayMessage(npc, message, player)
	log(npc.displayName, "Displaying message to " .. player.Name .. ": " .. message)

	-- Display chat bubble
	ChatService:Chat(npc.model.Head, message, Enum.ChatColor.Blue)

	-- Send message to client for chat area display
	NPCChatEvent:FireClient(player, npc.displayName, message)
end

function NPCManager:start()
	for _, npc in pairs(self.npcs) do
		log(npc.displayName, "Started and ready for interactions")
	end
end

return NPCManager
