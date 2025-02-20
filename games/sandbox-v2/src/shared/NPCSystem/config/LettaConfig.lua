return {
    BASE_URL = "https://roblox.ella-ai-care.com",
    ENDPOINTS = {
        CHAT = "/letta/v1/chat/v3",
        AGENTS = "/letta/v1/agents",
        SNAPSHOT = "/letta/v1/snapshot/game",
        GROUP_UPDATE = "/letta/v1/npc/group/update",
        STATUS_UPDATE = "/letta/v1/npc/status/update",
        PLAYER_DESCRIPTION = "/letta/v1/get_player_description"
    },
    DEFAULT_HEADERS = {
        ["Content-Type"] = "application/json"
    }
} 