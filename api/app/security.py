# security.py
import os
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv

load_dotenv()
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")

def check_allowed_ips(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource."
        )