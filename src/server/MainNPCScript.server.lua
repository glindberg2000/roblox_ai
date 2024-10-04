-- Script Name: MainNPCScript
-- Script Location: ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")

local NPCManager = require(ReplicatedStorage:WaitForChild("NPCManager"))
local NPCConfigurations = require(script.Parent:WaitForChild("NPCConfigurations"))

local NPCFolder = workspace:FindFirstChild("NPCs") or Instance.new("Folder")
NPCFolder.Name = "NPCs"
NPCFolder.Parent = workspace

local initializedNPCs = {}

local function spawnNPC(config)
	print("Spawning NPC: " .. config.displayName)

	local model = ServerStorage:FindFirstChild(config.model)
	if not model then
		warn("Model not found in ServerStorage for NPC: " .. config.displayName)
		return
	end

	local npcModel = model:Clone()
	npcModel.Parent = NPCFolder

	-- Set the PrimaryPart if it's not already set
	if not npcModel.PrimaryPart then
		local part = npcModel:FindFirstChildWhichIsA("BasePart")
		if part then
			npcModel.PrimaryPart = part
		else
			warn("No suitable part found for PrimaryPart in model: " .. config.displayName)
			return
		end
	end

	-- Now set the CFrame of the model
	npcModel:SetPrimaryPartCFrame(CFrame.new(config.spawnPosition))

	local npc = NPCManager.new(npcModel, config.npcId, config.displayName, config.responseRadius)
	npc:start()

	return npc
end

for _, config in ipairs(NPCConfigurations) do
	local npc = spawnNPC(config)
	if npc then
		table.insert(initializedNPCs, npc)
	end
end

local function setupChatConnections()
	local function onPlayerChatted(player, message)
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if not playerPosition then
			return
		end

		local closestNPC = nil
		local closestDistance = math.huge

		for _, npc in ipairs(initializedNPCs) do
			if npc.model.PrimaryPart then
				local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
				if distance <= npc.responseRadius and distance < closestDistance then
					closestNPC = npc
					closestDistance = distance
				end
			end
		end

		if closestNPC then
			closestNPC:handleNPCInteraction(player, message)
		end
	end

	Players.PlayerAdded:Connect(function(player)
		player.Chatted:Connect(function(message)
			onPlayerChatted(player, message)
		end)
	end)

	for _, player in ipairs(Players:GetPlayers()) do
		player.Chatted:Connect(function(message)
			onPlayerChatted(player, message)
		end)
	end
end

setupChatConnections()

print("NPC system initialized with " .. #initializedNPCs .. " NPCs")

-- Function to spawn a new NPC at runtime
local function spawnNewNPC(npcConfig)
	local npc = spawnNPC(npcConfig)
	if npc then
		table.insert(initializedNPCs, npc)
		print("New NPC spawned: " .. npc.displayName)
	end
end

-- Expose the spawnNewNPC function to other scripts
_G.spawnNewNPC = spawnNewNPC
