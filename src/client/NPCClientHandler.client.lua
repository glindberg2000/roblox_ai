-- NPCClientHandler.client.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

NPCChatEvent.OnClientEvent:Connect(function(npcName, message)
	print("Received NPC message on client: " .. npcName .. " - " .. message)

	-- Get the default text channel
	local textChannel = TextChatService.TextChannels.RBXGeneral
	if textChannel then
		-- Display the NPC message as a system message in the chatbox
		textChannel:DisplaySystemMessage(npcName .. ": " .. message)
	else
		warn("RBXGeneral text channel not found.")
	end

	print("NPC Chat Displayed in Chatbox - " .. npcName .. ": " .. message)
end)

print("NPC Client Chat Handler loaded")
