local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

-- Load core services
local services = {}
for _, module in ipairs(script.services:GetChildren()) do
    if module:IsA("ModuleScript") then
        services[module.Name] = require(module)
    end
end

-- Initialize services
for name, service in pairs(services) do
    if type(service.Initialize) == "function" then
        local success, err = pcall(function()
            service:Initialize()
        end)
        if not success then
            warn(string.format("Failed to initialize %s: %s", name, err))
        end
    end
end

return services 