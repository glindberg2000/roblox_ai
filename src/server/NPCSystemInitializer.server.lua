-- NPCSystemInitializer.server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Create RemoteEvents
local NPCChatEvent = Instance.new("RemoteEvent")
NPCChatEvent.Name = "NPCChatEvent"
NPCChatEvent.Parent = ReplicatedStorage

-- Create a flag to determine which system to use
local UseV3System = Instance.new("BoolValue")
UseV3System.Name = "UseV3System"
UseV3System.Value = true -- Set this to true to use V3, false to use V2
UseV3System.Parent = ReplicatedStorage

print("NPC System initialized. Using V" .. (UseV3System.Value and "3" or "2") .. " system.")
