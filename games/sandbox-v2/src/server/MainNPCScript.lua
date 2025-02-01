local ClusterSystem = require(script.Parent.ServerModules.ClusterSystem)
local GroupChatManager = require(script.Parent.ServerModules.GroupChatManager)

-- Initialize systems
GroupChatManager:start_scheduler()
print("NPC system initialized") 