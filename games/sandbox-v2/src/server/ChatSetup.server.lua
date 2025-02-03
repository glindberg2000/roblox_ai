local ChatService = game:GetService("Chat")
local TextChatService = game:GetService("TextChatService")
local ServerScriptService = game:GetService("ServerScriptService")
local LoggerService = require(game:GetService("ReplicatedStorage").Shared.NPCSystem.services.LoggerService)

LoggerService:info("SYSTEM", "Setting up chat service")

-- Enable bubble chat
ChatService.BubbleChatEnabled = true

-- Enable TextChatService
TextChatService.ChatVersion = Enum.ChatVersion.TextChatService

LoggerService:info("SYSTEM", "Chat setup completed")