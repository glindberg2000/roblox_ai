local PerformanceMonitor = {}
local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")

local metrics = {
    frameRate = {},
    serverLoad = {},
    memoryUsage = {},
    networkBandwidth = {}
}

function PerformanceMonitor:startTracking()
    RunService.Heartbeat:Connect(function()
        -- Track FPS
        table.insert(metrics.frameRate, 1/RunService.Heartbeat:Wait())
        if #metrics.frameRate > 60 then table.remove(metrics.frameRate, 1) end
        
        -- Track Server Stats
        table.insert(metrics.serverLoad, Stats:GetTotalMemoryUsageMb())
        table.insert(metrics.memoryUsage, Stats.DataReceiveKbps)
        table.insert(metrics.networkBandwidth, Stats.DataSendKbps)
        
        -- Keep only last minute of data
        if #metrics.serverLoad > 60 then table.remove(metrics.serverLoad, 1) end
        if #metrics.memoryUsage > 60 then table.remove(metrics.memoryUsage, 1) end
        if #metrics.networkBandwidth > 60 then table.remove(metrics.networkBandwidth, 1) end
    end)
end

function PerformanceMonitor:getMetrics()
    local function average(t)
        local sum = 0
        for _, v in ipairs(t) do sum = sum + v end
        return #t > 0 and sum / #t or 0
    end
    
    return {
        avgFPS = average(metrics.frameRate),
        avgServerLoad = average(metrics.serverLoad),
        avgMemory = average(metrics.memoryUsage),
        avgNetwork = average(metrics.networkBandwidth)
    }
end

return PerformanceMonitor 