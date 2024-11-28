local ChatService = game:GetService("Chat")
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

Logger:log("SYSTEM", "Setting up chat service")

-- Enable bubble chat without checking ChatVersion
ChatService.BubbleChatEnabled = true

Logger:log("SYSTEM", "Chat setup completed")