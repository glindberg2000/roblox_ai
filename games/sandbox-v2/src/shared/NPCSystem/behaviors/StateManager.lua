local StateManager = {}

function StateManager.new(npc, config)
    local self = {
        npc = npc,
        config = config,
        currentState = nil,
        stateStartTime = 0,
        nextStateChange = 0
    }
    
    function self:initialize()
        local npcConfig = Config.GetNPCConfig(self.npc.npcType)
        self:setState(npcConfig.DefaultState)
    end
    
    function self:setState(newState)
        if self.currentState then
            self:cleanupState(self.currentState)
        end
        
        self.currentState = newState
        self.stateStartTime = os.time()
        self:initializeState(newState)
        
        -- Update NPC status
        self.npc:updateStatus({
            current_state = newState,
            state_start_time = self.stateStartTime
        })
    end
    
    function self:initializeState(state)
        if state == "Explore" then
            -- Initialize exploration behavior
        elseif state == "Patrol" then
            -- Initialize patrol behavior
        -- etc
        end
    end
    
    -- Additional methods for state management
    
    return self
end

return StateManager 