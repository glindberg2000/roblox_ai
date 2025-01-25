import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import logging
from .cache import init_static_cache
import requests
from requests.exceptions import RequestException

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("roblox_app")

# Load environment variables
load_dotenv()

# Get Letta configuration from environment
LETTA_CONFIG = {
    'host': os.getenv('LETTA_SERVER_HOST', 'localhost'),
    'port': int(os.getenv('LETTA_SERVER_PORT', '8283')),
    'base_url': os.getenv('LETTA_BASE_URL', 'http://localhost:8283')
}

logger.info("Letta Server Configuration:")
logger.info(f"Base URL: {LETTA_CONFIG['base_url']}")
logger.info(f"Host: {LETTA_CONFIG['host']}")
logger.info(f"Port: {LETTA_CONFIG['port']}")

# Import after logging setup
from .config import BASE_DIR

# Setup paths - use BASE_DIR from config
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Debug information
logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Static directory: {STATIC_DIR}")
logger.info(f"Directory contents: {os.listdir(BASE_DIR)}")

# Create FastAPI app
app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after FastAPI initialization
from .routers import router
from .dashboard_router import router as dashboard_router
from .routers_v4 import router as router_v4
from .letta_router import router as letta_router

# Include routers
app.include_router(dashboard_router)
app.include_router(router)
app.include_router(router_v4)
app.include_router(letta_router)

# Create static directory if it doesn't exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# main.py
from fastapi import Depends
from .security import check_allowed_ips

@app.get("/")
@app.get("/dashboard")
async def serve_dashboard(request: Request, allowed_ips=Depends(check_allowed_ips)):
    """Serve the dashboard"""
    return templates.TemplateResponse("dashboard_new.html", {"request": request})


#Route handlers
# @app.get("/")
# @app.get("/dashboard")
# async def serve_dashboard(request: Request):
#     """Serve the dashboard"""
#     return templates.TemplateResponse("dashboard_new.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    """Initialize on server startup"""
    logger.info("Starting Roblox API server...")
    
    # Test Letta connection
    try:
        logger.info(f"Testing connection to Letta server at {LETTA_CONFIG['base_url']}")
        # Just test the base URL since we know it works
        response = requests.get(LETTA_CONFIG['base_url'], timeout=10)  # Increased timeout
        if response.ok:
            logger.info("Successfully connected to Letta server")
            # Try to get version info
            try:
                version_response = requests.get(f"{LETTA_CONFIG['base_url']}/api/version")
                if version_response.ok:
                    logger.info(f"Letta server version: {version_response.json()}")
            except:
                pass  # Version check is optional
        else:
            logger.warning(f"Letta server returned status {response.status_code}")
    except RequestException as e:
        logger.error(f"Failed to connect to Letta server: {str(e)}")
    
    init_static_cache()
    logger.info("Static caches initialized")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RobloxAPI app is shutting down...")

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Debug the static file serving
logger.info(f"Static files being served from: {STATIC_DIR}")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Add cache control middleware
@app.middleware("http")
async def add_cache_control_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

