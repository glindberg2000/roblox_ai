local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local ServerScriptService = game:GetService("ServerScriptService")

print("NPCSystemInitializer: Starting initialization...")

-- Wait for critical paths
local Shared = ReplicatedStorage:WaitForChild("Shared", 10)
if not Shared then
	print("Failed to find Shared folder")
	return
end

local NPCSystem = Shared:WaitForChild("NPCSystem", 10)
if not NPCSystem then
	print("Failed to find NPCSystem folder")
	return
end

print("Found NPCSystem")
print("Path: " .. tostring(NPCSystem:GetFullName()))
print("NPCSystem children:")
for _, child in ipairs(NPCSystem:GetChildren()) do
	print("Child: " .. tostring(child.Name) .. " (" .. tostring(child.ClassName) .. ")")
end

-- Try to load Logger first
print("NPCSystemInitializer: Attempting to load LoggerService...")

local services = NPCSystem:WaitForChild("services")
if not services then
	print("Failed to find services folder")
	return
end

local LoggerService = services:WaitForChild("LoggerService")
if not LoggerService then
	print("Failed to find LoggerService")
	return
end

local success, Logger = pcall(function()
	return require(LoggerService)
end)

if not success then
	print("Failed to load LoggerService - error: " .. tostring(Logger))
	return
end

print("NPCSystemInitializer: LoggerService loaded")

-- Initialize storage structure first
local function ensureStorage()
	print("NPCSystemInitializer: Setting up storage...")
	
	-- Create Assets/npcs folder structure
	local Assets = ServerStorage:FindFirstChild("Assets") or 
				   Instance.new("Folder", ServerStorage)
	Assets.Name = "Assets"
	Assets.Parent = ServerStorage
	
	local npcs = Assets:FindFirstChild("npcs") or 
				 Instance.new("Folder", Assets)
	npcs.Name = "npcs"
	npcs.Parent = Assets
	
	-- Create NPCs folder in workspace if it doesn't exist
	if not workspace:FindFirstChild("NPCs") then
		local NPCsFolder = Instance.new("Folder")
		NPCsFolder.Name = "NPCs"
		NPCsFolder.Parent = workspace
		print("Created NPCs folder in workspace")
	end
	
	print("NPCSystemInitializer: Storage setup complete")
	return npcs
end

local npcsFolder = ensureStorage()

-- Initialize events for NPC chat and interaction
if not ReplicatedStorage:FindFirstChild("NPCChatEvent") then
	local NPCChatEvent = Instance.new("RemoteEvent")
	NPCChatEvent.Name = "NPCChatEvent"
	NPCChatEvent.Parent = ReplicatedStorage
	print("Created NPCChatEvent")
end

if not ReplicatedStorage:FindFirstChild("EndInteractionEvent") then
	local EndInteractionEvent = Instance.new("RemoteEvent")
	EndInteractionEvent.Name = "EndInteractionEvent"
	EndInteractionEvent.Parent = ReplicatedStorage
	print("Created EndInteractionEvent")
end

print("NPCSystemInitializer: Events created")

-- Try to load NPCManagerV3
print("NPCSystemInitializer: Attempting to load NPCManagerV3...")
print("NPCManagerV3 path: " .. tostring(NPCSystem.NPCManagerV3:GetFullName()))

local success, NPCManagerV3 = pcall(function()
	return require(NPCSystem.NPCManagerV3)
end)

if not success then
	print("Failed to load NPCManagerV3: " .. tostring(NPCManagerV3))
	return
end

print("NPCSystemInitializer: NPCManagerV3 loaded")

-- Create and store NPCManager instance
local npcManager = NPCManagerV3.getInstance()
if not npcManager then
	print("Failed to get NPCManagerV3 instance")
	return
end

_G.NPCManager = npcManager

print("NPCSystemInitializer: Initialization complete")
