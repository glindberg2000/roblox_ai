-- Script Name: NPCManager
-- Script Location: ReplicatedStorage

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")

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

function NPCManager.new(model, npcId, displayName, responseRadius)
	local self = setmetatable({}, NPCManager)
	self.model = model
	self.npcId = npcId
	self.displayName = displayName
	self.responseRadius = responseRadius or RESPONSE_RADIUS
	self.activeConversations = {}
	self.lastResponseTime = 0

	log(self.displayName, "NPC created")

	self:setupClickDetector()
	return self
end

function NPCManager:setupClickDetector()
	log(self.displayName, "Setting up ClickDetector")

	local part = self:getInteractionPart()
	if not part then
		warn(self.displayName .. ": Failed to set up ClickDetector - No suitable part found")
		return
	end

	local clickDetector = Instance.new("ClickDetector")
	clickDetector.MaxActivationDistance = self.responseRadius
	clickDetector.Parent = part

	log(self.displayName, "ClickDetector parented to " .. part.Name)

	clickDetector.MouseClick:Connect(function(player)
		log(self.displayName, "Clicked by " .. player.Name)
		self:handleNPCInteraction(player, "Hello")
	end)
end

function NPCManager:getInteractionPart()
	return self.model.PrimaryPart
		or self.model:FindFirstChild("HumanoidRootPart")
		or self.model:FindFirstChild("Torso")
		or self.model:FindFirstChild("UpperTorso")
end

function NPCManager:handleNPCInteraction(player, message)
	log(self.displayName, "Handling interaction from " .. player.Name .. ": " .. message)

	local currentTime = tick()
	if currentTime - self.lastResponseTime < RESPONSE_COOLDOWN then
		log(self.displayName, "Ignoring message due to cooldown")
		return
	end

	local response = self:getResponseFromAI(message, player)
	if response then
		self:displayMessage(response, player)
		self:setActiveConversation(player)
		self.lastResponseTime = currentTime
	else
		log(self.displayName, "No response received from AI")
	end
end

function NPCManager:isInActiveConversation(player)
	local conversation = self.activeConversations[player.UserId]
	if not conversation then
		return false
	end

	local isActive = tick() - conversation.lastInteractionTime < CONVERSATION_TIMEOUT
	log(self.displayName, "Active conversation check for " .. player.Name .. ": " .. tostring(isActive))
	return isActive
end

function NPCManager:setActiveConversation(player)
	self.activeConversations[player.UserId] = {
		lastInteractionTime = tick(),
	}
	log(self.displayName, "Set active conversation with " .. player.Name)
end

function NPCManager:isMessageDirected(message)
	local lowerMessage = message:lower()
	local isDirected = lowerMessage:find(self.displayName:lower()) or lowerMessage:find(self.npcId:lower())
	log(self.displayName, "Message directed check: " .. tostring(isDirected))
	return isDirected
end

function NPCManager:getResponseFromAI(message, player)
	log(self.displayName, "Getting AI response for: " .. message)

	local data = {
		message = message,
		player_id = tostring(player.UserId),
		npc_id = self.npcId,
		npc_name = self.displayName,
		limit = 200,
	}

	local success, response = pcall(function()
		return HttpService:PostAsync(API_URL, HttpService:JSONEncode(data), Enum.HttpContentType.ApplicationJson, false)
	end)

	if success then
		local parsed = HttpService:JSONDecode(response)
		if parsed and parsed.message then
			log(self.displayName, "AI response received: " .. parsed.message)
			return parsed.message
		else
			warn(self.displayName .. ": Received invalid response from AI")
			return nil
		end
	else
		warn(self.displayName .. ": Failed to get response from AI: " .. tostring(response))
		return nil
	end
end

function NPCManager:displayMessage(message, player)
	log(self.displayName, "Displaying message to " .. player.Name .. ": " .. message)

	-- Display chat bubble
	local chatService = game:GetService("Chat")
	chatService:Chat(self.model.Head, message, Enum.ChatColor.Blue)

	-- Send message to client for chat area display
	NPCChatEvent:FireClient(player, self.displayName, message)
end

function NPCManager:start()
	log(self.displayName, "Started and ready for interactions")
end

return NPCManager
