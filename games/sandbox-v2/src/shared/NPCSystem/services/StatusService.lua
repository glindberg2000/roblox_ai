local StatusService = {}

StatusService.States = {
    EXPLORING = "Exploring",
    PATROLLING = "Patrolling",
    WANDERING = "Wandering",
    IDLE = "Idle",
    FOLLOWING = "Following",
    INTERACTING = "Interacting"
}

function StatusService:updateNPCStatus(npc, status)
    local statusData = {
        current_state = status.current_state,
        state_details = {
            start_time = status.state_start_time,
            location = npc.humanoid.RootPart.Position,
            target = status.target_position,
            path_progress = status.path_progress
        }
    }
    
    -- Send status update to backend
    self:sendStatusUpdate(npc.id, statusData)
end

return StatusService 