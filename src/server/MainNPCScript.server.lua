-- Script Name: MainNPCScript (v2.3)
-- Script Location: ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")

print("MainNPCScript starting...")

local NPCManager = require(ReplicatedStorage:WaitForChild("NPCManager"))
print("NPCManager loaded")

local NPCFolder = workspace:FindFirstChild("NPCs") or Instance.new("Folder")
NPCFolder.Name = "NPCs"
NPCFolder.Parent = workspace
print("NPCFolder created/found in workspace")

-- Create an instance of NPCManager
local npcManager = NPCManager.new()
print("NPCManager instance created")

-- Print out the NPCs that were created
for id, npc in pairs(npcManager.npcs) do
	print("NPC created: " .. npc.displayName .. " (ID: " .. id .. ")")
end

local function setupChatConnections()
	local function onPlayerChatted(player, message)
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if not playerPosition then
			return
		end

		local closestNPC = nil
		local closestDistance = math.huge

		for _, npc in pairs(npcManager.npcs) do
			if npc.model.PrimaryPart then
				local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
				if distance <= npc.responseRadius and distance < closestDistance then
					closestNPC = npc
					closestDistance = distance
				end
			end
		end

		if closestNPC then
			npcManager:handleNPCInteraction(closestNPC, player, message)
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

print("NPC system initialized with " .. #npcManager.npcs .. " NPCs")

-- Function to spawn a new NPC at runtime
local function spawnNewNPC(npcConfig)
	local npc = npcManager:createNPC(npcConfig)
	if npc then
		table.insert(npcManager.npcs, npc)
		print("New NPC spawned: " .. npc.displayName)
	end
end

-- Expose the spawnNewNPC function to other scripts
_G.spawnNewNPC = spawnNewNPC

print("MainNPCScript setup complete")
