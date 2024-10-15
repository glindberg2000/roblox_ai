-- StarterPlayerScripts/NPCClientHandler.client.lua

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

local NPCChatEvent = ReplicatedStorage:WaitForChild("NPCChatEvent")

NPCChatEvent.OnClientEvent:Connect(function(npcName, message)
	if message ~= "The interaction has ended." then
		print("Received NPC message on client: " .. npcName .. " - " .. message)

		local textChannel = TextChatService.TextChannels.RBXGeneral
		if textChannel then
			textChannel:DisplaySystemMessage(npcName .. ": " .. message)
		else
			warn("RBXGeneral text channel not found.")
		end

		print("NPC Chat Displayed in Chatbox - " .. npcName .. ": " .. message)
	else
		print("Interaction ended with " .. npcName)
	end
end)

print("NPC Client Chat Handler loaded")
