local Logger = {}
Logger.logs = {}
Logger.maxBufferSize = 100 -- Set a limit for the buffer

-- Add log entry to buffer
function Logger.log(message)
	table.insert(Logger.logs, message)

	-- Send logs when buffer reaches the max size
	if #Logger.logs >= Logger.maxBufferSize then
		Logger.flushLogs()
	end
end

-- Send logs to heartbeat or external function
function Logger.flushLogs()
	-- Implement the logic to send logs via heartbeat or other methods
	for _, log in ipairs(Logger.logs) do
		print("Sending log:", log) -- Example: replace this with actual sending logic
	end

	-- Clear the buffer after sending
	Logger.logs = {}
end

-- Optional: Schedule regular log flushing
function Logger.startLogFlushing(interval)
	game:GetService("RunService").Heartbeat:Connect(function()
		Logger.flushLogs()
	end)
end

return Logger
