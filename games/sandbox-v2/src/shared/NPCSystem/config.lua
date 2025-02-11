local Config = {
    -- Behavior system configuration
    Behaviors = {
        -- Global behavior settings
        EnableBehaviors = true,
        MaxMovementThreads = 5,
        
        -- Movement States
        States = {
            Explore = {
                Enabled = true,
                MaxRadius = 200, -- Larger radius for exploration
                MinRadius = 100, -- Minimum distance to travel
                JumpProbability = 0.1,
                PathfindingTimeout = 10,
                UpdateInterval = 30, -- Longer intervals for exploration
            },
            
            Patrol = {
                Enabled = true,
                Waypoints = {}, -- Filled per NPC
                WaitTime = 5, -- Time to wait at each point
                JumpProbability = 0.05,
                LoopPatrol = true,
            },
            
            Wander = {
                Enabled = true,
                Radius = 40,
                MinRadius = 10,
                JumpProbability = 0.15,
                UpdateInterval = 10,
            },
            
            Idle = {
                Enabled = true,
                SmallMovementRadius = 3,
                SmallMovementProbability = 0.3,
                JumpProbability = 0.05,
                EmoteProbability = 0.1,
                MinIdleTime = 5,
                MaxIdleTime = 30,
            }
        },
        
        -- Per-NPC configurations
        NPCDefaults = {
            DefaultState = "Wander",
            AllowedStates = {"Wander", "Idle"},
            StateTransitions = {
                MinStateTime = 30,
                MaxStateTime = 120,
            }
        },
        
        -- Specific NPC overrides
        NPCOverrides = {
            ["Guard"] = {
                DefaultState = "Patrol",
                AllowedStates = {"Patrol", "Idle"},
                Patrol = {
                    Waypoints = {
                        {x = 0, y = 0, z = 0},
                        {x = 10, y = 0, z = 10},
                        -- etc
                    }
                }
            },
            ["Shopkeeper"] = {
                DefaultState = "Idle",
                AllowedStates = {"Idle", "Wander"},
                Wander = {
                    Radius = 10, -- Smaller radius for shop area
                }
            }
        }
    },

    -- Other existing config options...
    UseNewActionSystem = false
}

-- Helper functions
function Config.GetNPCConfig(npcType)
    local override = Config.Behaviors.NPCOverrides[npcType]
    if override then
        -- Deep merge override with defaults
        return Config.DeepMerge(Config.Behaviors.NPCDefaults, override)
    end
    return Config.Behaviors.NPCDefaults
end

function Config.DeepMerge(default, override)
    -- Implementation of deep table merge
    local result = table.clone(default)
    -- ... merge logic ...
    return result
end

return Config 