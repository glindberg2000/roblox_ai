local ENABLED_CATEGORIES = {
    ERROR = true,      -- Keep errors always enabled
    SYSTEM = true,     -- Keep core system messages
    ANIMATION = true,  -- Keep animation logs for debugging
    CHAT = true,       -- Keep chat logs
    
    -- Disable noisy categories
    RANGE = false,
    DEBUG = false, 
    MOVEMENT = false,
    INTERACTION = false,
    THREAD = false,
    STATE = false,
    DATABASE = false,
    ASSET = false,
    API = false,
    NPC = false
} 