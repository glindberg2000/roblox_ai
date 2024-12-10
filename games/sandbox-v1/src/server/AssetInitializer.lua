-- Reduce logging in asset initialization
local function initializeAssets()
    -- Only log start and completion
    Logger:log("SYSTEM", "Starting asset initialization...")
    
    -- Asset initialization code...
    
    Logger:log("SYSTEM", "Asset initialization complete")
end 