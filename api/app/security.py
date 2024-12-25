# security.py
import os
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv
import ipaddress
import logging

load_dotenv()
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")
logger = logging.getLogger(__name__)

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