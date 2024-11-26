local Logger = require(game:GetService("ServerScriptService"):WaitForChild("Logger"))

-- Enable specific log types you want to see
Logger:enableLogType(Logger.LOG_TYPES.VISION)
Logger:enableLogType(Logger.LOG_TYPES.INTERACTION)
Logger:enableLogType(Logger.LOG_TYPES.MOVEMENT)

-- Example usage
Logger:log("NPC system starting up", Logger.LOG_TYPES.SYSTEM) 