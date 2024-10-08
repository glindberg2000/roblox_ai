-- MainNPCScript.server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local NPCManager = require(ReplicatedStorage:WaitForChild("NPCManager"))
local NPCManagerV2 = require(ReplicatedStorage:WaitForChild("NPCManagerV2"))

local npcManager = NPCManager.new()
local npcManagerV2 = NPCManagerV2.new()

local function checkPlayerProximity()
	for _, player in ipairs(Players:GetPlayers()) do
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if playerPosition then
			for _, npc in pairs(npcManager.npcs) do
				if npc.model and npc.model.PrimaryPart then
					local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
					if distance <= npc.responseRadius and not npc.isInteracting then
						npcManager:handleProximityInteraction(npc, player)
					end
				end
			end
			for _, npc in pairs(npcManagerV2.npcs) do
				if npc.model and npc.model.PrimaryPart then
					local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
					if distance <= npc.responseRadius and not npc.isInteracting then
						npcManagerV2:handleProximityInteraction(npc, player)
					end
				end
			end
		end
	end
end

local function onPlayerChatted(player, message)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not playerPosition then
		return
	end

	local closestNPC, closestDistance = nil, math.huge
	local closestNPCV2, closestDistanceV2 = nil, math.huge

	for _, npc in pairs(npcManager.npcs) do
		if npc.model and npc.model.PrimaryPart then
			local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
			if distance <= npc.responseRadius and distance < closestDistance then
				closestNPC, closestDistance = npc, distance
			end
		end
	end

	for _, npc in pairs(npcManagerV2.npcs) do
		if npc.model and npc.model.PrimaryPart then
			local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
			if distance <= npc.responseRadius and distance < closestDistanceV2 then
				closestNPCV2, closestDistanceV2 = npc, distance
			end
		end
	end

	if closestDistance < closestDistanceV2 and closestNPC then
		npcManager:handleNPCInteraction(closestNPC, player, message)
	elseif closestNPCV2 then
		npcManagerV2:handleNPCInteraction(closestNPCV2, player, message)
	end
end

local function setupChatConnections()
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

local function updateNPCs()
	while true do
		checkPlayerProximity()
		for _, npc in pairs(npcManager.npcs) do
			npcManager:updateNPCState(npc)
		end
		for _, npc in pairs(npcManagerV2.npcs) do
			npcManagerV2:updateNPCState(npc)
		end
		wait(1) -- Update every second
	end
end

spawn(updateNPCs)

print("NPC system v1 initialized with " .. #npcManager.npcs .. " NPCs")
print("NPC system v2 initialized with " .. #npcManagerV2.npcs .. " NPCs")
