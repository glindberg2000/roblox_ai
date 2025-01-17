# security.py
import os
from fastapi import Request, HTTPException, status, Security, Depends
from dotenv import load_dotenv
import ipaddress
import logging
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from typing import Optional
from functools import wraps
from .config import ADMIN_API_KEY, GAME_API_KEY

load_dotenv()
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")
logger = logging.getLogger(__name__)

# Define security schemes
admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)
game_key_header = APIKeyHeader(name="X-Game-Key", auto_error=False)

# Public endpoints that don't require auth
PUBLIC_ENDPOINTS = {
    "/api/chat/v2",  # Main chat endpoint
    "/api/npcs/list",  # Public NPC listing
    "/api/assets/public",  # Public asset info
}

# Admin-only endpoints that require full auth
ADMIN_ENDPOINTS = {
    "/api/npcs",  # NPC management
    "/api/assets",  # Asset management
    "/api/games",  # Game management
    "/dashboard",  # Admin dashboard
}

async def verify_admin_key(api_key: Optional[str] = Security(admin_key_header)) -> bool:
    """Verify admin API key"""
    if not api_key or api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin key"
        )
    return True

async def verify_game_key(api_key: Optional[str] = Security(game_key_header)) -> bool:
    """Verify game API key - less privileged than admin"""
    if not api_key or api_key != GAME_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid game key"
        )
    return True

def require_admin(endpoint):
    """Decorator for admin-only endpoints"""
    @wraps(endpoint)
    async def secured_endpoint(*args, **kwargs):
        await verify_admin_key()
        return await endpoint(*args, **kwargs)
    return secured_endpoint

def require_game_key(endpoint):
    """Decorator for game-authenticated endpoints"""
    @wraps(endpoint)
    async def secured_endpoint(*args, **kwargs):
        await verify_game_key()
        return await endpoint(*args, **kwargs)
    return secured_endpoint

def is_ip_in_network(ip: str, network: str) -> bool:
    """Check if IP is in network range"""
    try:
        # Handle both IPv4 and IPv6
        ip_addr = ipaddress.ip_address(ip)
        network = ipaddress.ip_network(network, strict=False)
        return ip_addr in network
    except ValueError:
        return False

def check_allowed_ips(request: Request):
    # Temporarily allow all access
    logger.warn(f"SECURITY DISABLED - Allowing access from {request.client.host}")
    return

    # Commented out security checks
    # if request.url.path.startswith("/letta/v1/chat"):
    #     logger.debug(f"Allowing chat endpoint access from {request.client.host}")
    #     return
    # ...rest of the function