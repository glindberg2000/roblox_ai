-- ServerScriptService/MainNPCScript.server.lua
-- At the top of MainNPCScript.server.lua
local ServerScriptService = game:GetService("ServerScriptService")
local InteractionController = require(ServerScriptService:WaitForChild("InteractionController"))

local success, result = pcall(function()
	return require(ServerScriptService:WaitForChild("InteractionController", 5))
end)

if success then
	InteractionController = result
	print("InteractionController loaded successfully")
else
	warn("Failed to load InteractionController:", result)
	-- Provide a basic implementation to prevent further errors
	InteractionController = {
		new = function()
			return {
				canInteract = function()
					return true
				end,
				startInteraction = function()
					return true
				end,
				endInteraction = function() end,
				getInteractingNPC = function()
					return nil
				end,
			}
		end,
	}
end

-- Rest of your MainNPCScript code...
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")

local Logger = require(ServerScriptService:WaitForChild("Logger"))

-- Move ensureStorage to the top, before NPC initialization
local function ensureStorage()
    local ServerStorage = game:GetService("ServerStorage")
    
    -- Create Assets/npcs folder structure
    local Assets = ServerStorage:FindFirstChild("Assets") or 
                   Instance.new("Folder", ServerStorage)
    Assets.Name = "Assets"
    
    local npcs = Assets:FindFirstChild("npcs") or 
                 Instance.new("Folder", Assets)
    npcs.Name = "npcs"
end

-- Call ensureStorage first
ensureStorage()

-- Then initialize NPC system
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))
print("Starting NPC initialization")
local npcManagerV3 = NPCManagerV3.new()
print("NPC Manager created")

for npcId, npcData in pairs(npcManagerV3.npcs) do
	print("NPC spawned: " .. npcData.displayName)
end

local interactionController = npcManagerV3.interactionController

Logger:log("NPC system V3 initialized")

local function checkPlayerProximity()
	for _, player in ipairs(Players:GetPlayers()) do
		local playerPosition = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if playerPosition then
			for _, npc in pairs(npcManagerV3.npcs) do
				if npc.model and npc.model.PrimaryPart then
					local distance = (playerPosition.Position - npc.model.PrimaryPart.Position).Magnitude
					if distance <= npc.responseRadius and not npc.isInteracting then
						if interactionController:canInteract(player) then
							npcManagerV3:handleNPCInteraction(npc, player, "Hello")
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
end

local function setupChatConnections()
	Players.PlayerAdded:Connect(function(player)
		player.Chatted:Connect(function(message)
			onPlayerChatted(player, message)
		end)
	end)
end

setupChatConnections()

local function updateNPCs()
	while true do
		checkPlayerProximity()
		for _, npc in pairs(npcManagerV3.npcs) do
			npcManagerV3:updateNPCState(npc)
		end
		wait(1)
	end
end

spawn(updateNPCs)

-- Handle player-initiated interaction ending
local EndInteractionEvent = Instance.new("RemoteEvent")
EndInteractionEvent.Name = "EndInteractionEvent"
EndInteractionEvent.Parent = ReplicatedStorage

EndInteractionEvent.OnServerEvent:Connect(function(player)
	local interactingNPC = interactionController:getInteractingNPC(player)
	if interactingNPC then
		npcManagerV3:endInteraction(interactingNPC, player)
	end
end)

Logger:log("NPC system V3 main script running")
