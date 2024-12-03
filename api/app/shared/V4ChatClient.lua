function V4ChatClient:SendMessage(data)
    print("V4ChatClient:SendMessage called")
    -- Try Letta first
    local lettaResponse = handleLettaChat(data)
    if lettaResponse then
        return lettaResponse
    end

    print("Letta failed, falling back to V4")
    -- Fall back to V4 if Letta fails
    return self:SendMessageV4(data)
end 