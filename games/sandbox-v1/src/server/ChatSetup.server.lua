local ChatService = game:GetService("Chat")
local ServerScriptService = game:GetService("ServerScriptService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

LoggerService:info("SYSTEM", "Setting up chat service")

-- Enable bubble chat without using deprecated method
ChatService.BubbleChatEnabled = true

LoggerService:info("SYSTEM", "Chat setup completed")