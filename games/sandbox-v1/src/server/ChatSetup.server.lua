local ChatService = game:GetService("Chat")
local ServerScriptService = game:GetService("ServerScriptService")
local Logger = require(ServerScriptService:WaitForChild("Logger"))

Logger:log("SYSTEM", "Setting up chat service")

-- Example: Enabling chat (if needed)
if ChatService then
    local success, result = pcall(function()
        ChatService:ChatVersion("TextChatService")
    end)
    
    if success then
        Logger:log("SYSTEM", "Chat service initialized successfully")
    else
        Logger:log("ERROR", string.format("Unable to initialize chat service: %s", tostring(result)))
    end
else
    Logger:log("ERROR", "Unable to get Chat service: service not available")
end

Logger:log("SYSTEM", "Chat setup completed")