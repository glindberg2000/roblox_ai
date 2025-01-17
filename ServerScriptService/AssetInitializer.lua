local ServerScriptService = game:GetService("ServerScriptService")
-- Ensure the correct path or service is accessed
local AssetDatabase = ServerScriptService:FindFirstChild("AssetDatabase")
if not AssetDatabase then
    warn("AssetDatabase not found in ServerScriptService")
end 