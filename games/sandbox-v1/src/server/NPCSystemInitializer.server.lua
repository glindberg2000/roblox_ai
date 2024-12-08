local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))
local NPCManagerV3 = require(ReplicatedStorage:WaitForChild("NPCManagerV3"))

-- Initialize storage structure first
local function ensureStorage()
	-- Create Assets/npcs folder structure
	local Assets = ServerStorage:FindFirstChild("Assets") or 
				   Instance.new("Folder", ServerStorage)
	Assets.Name = "Assets"
	
	local npcs = Assets:FindFirstChild("npcs") or 
				 Instance.new("Folder", Assets)
	npcs.Name = "npcs"
	
	-- Get list of required models from NPCDatabase
	local npcDatabase = require(ReplicatedStorage:WaitForChild("NPCDatabaseV3"))
	
	-- Scan the npcs folder for available models
	local availableModels = {}
	for _, model in ipairs(npcs:GetChildren()) do
		availableModels[model.Name] = true
		Logger:log("ASSET", string.format("Found model: %s", model.Name))
	end
	
	-- Check which required models are missing
	for _, npc in ipairs(npcDatabase.npcs) do
		if not availableModels[npc.model] then
			Logger:log("ERROR", string.format("Missing required model '%s' for NPC: %s", 
				npc.model, npc.displayName))
		end
	end
	
	return npcs
end

local npcsFolder = ensureStorage()

-- Initialize events for NPC chat and interaction
if not ReplicatedStorage:FindFirstChild("NPCChatEvent") then
	local NPCChatEvent = Instance.new("RemoteEvent")
	NPCChatEvent.Name = "NPCChatEvent"
	NPCChatEvent.Parent = ReplicatedStorage
	Logger:log("SYSTEM", "Created NPCChatEvent")
end

if not ReplicatedStorage:FindFirstChild("EndInteractionEvent") then
	local EndInteractionEvent = Instance.new("RemoteEvent")
	EndInteractionEvent.Name = "EndInteractionEvent"
	EndInteractionEvent.Parent = ReplicatedStorage
	Logger:log("SYSTEM", "Created EndInteractionEvent")
end

Logger:log("SYSTEM", "NPC System initialized. Using V3 system.")

-- Create and store NPCManager instance
local npcManager = NPCManagerV3.getInstance()
_G.NPCManager = npcManager
