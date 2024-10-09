-- MainNPCScript.server.lua (V3)
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local NPCManagerV2 = require(ReplicatedStorage:WaitForChild("NPCManagerV2"))
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))

local npcManagerV2 = NPCManagerV2.new()
local npcManagerV3 = NPCManagerV3.new()

local UseV3System = ReplicatedStorage:WaitForChild("UseV3System")

local function checkPlayerProximity()
	for _, player in ipairs(Players:GetPlayers()) do
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if playerPosition then
			if UseV3System.Value then
				for _, npc in pairs(npcManagerV3.npcs) do
					if npc.model and npc.model.PrimaryPart then
						local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
						print(npc.displayName .. " distance to " .. player.Name .. ": " .. distance)
						if distance <= npc.responseRadius and not npc.isInteracting then
							print(npc.displayName .. " initiating interaction with " .. player.Name)
							npcManagerV3:handleNPCInteraction(npc, player, "Hello")
						end
					end
				end
			else
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
end

local function onPlayerChatted(player, message)
	local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not playerPosition then
		return
	end

	if UseV3System.Value then
		local closestNPC, closestDistance = nil, math.huge

		for _, npc in pairs(npcManagerV3.npcs) do
			if npc.model and npc.model.PrimaryPart then
				local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
				if distance <= npc.responseRadius and distance < closestDistance then
					closestNPC, closestDistance = npc, distance
				end
			end
		end

		if closestNPC then
			npcManagerV3:handleNPCInteraction(closestNPC, player, message)
		end
	else
		local closestNPC, closestDistance = nil, math.huge

		for _, npc in pairs(npcManagerV2.npcs) do
			if npc.model and npc.model.PrimaryPart then
				local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
				if distance <= npc.responseRadius and distance < closestDistance then
					closestNPC, closestDistance = npc, distance
				end
			end
		end

		if closestNPC then
			npcManagerV2:handleNPCInteraction(closestNPC, player, message)
		end
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
		if UseV3System.Value then
			print("Updating V3 NPCs, Count: " .. npcManagerV3:getNPCCount())
			for _, npc in pairs(npcManagerV3.npcs) do
				npcManagerV3:updateNPCState(npc)
			end
		else
			print("Updating V2 NPCs, Count: " .. #npcManagerV2.npcs)
			for _, npc in pairs(npcManagerV2.npcs) do
				npcManagerV2:updateNPCState(npc)
			end
		end
		wait(1) -- Update every second
	end
end

spawn(updateNPCs)

print("NPC system " .. (UseV3System.Value and "V3" or "V2") .. " initialized")
