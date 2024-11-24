local ChatService = game:GetService("Chat")

-- Example: Enabling chat (if needed)
if ChatService then
    ChatService:ChatVersion("TextChatService") -- Use appropriate API methods for enabling TextChat
    print("Chat setup completed.")
else
    warn("Chat service not available.")
end