from typing import Any
from letta import create_client
from config import settings

def get_direct_client() -> Any:
    """Get a direct Letta client instance"""
    client = create_client(
        base_url=settings.LETTA_BASE_URL,
        api_key=settings.LETTA_API_KEY
    )
    return client 