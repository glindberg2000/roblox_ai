import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

# Create logger for our app
logger = logging.getLogger("roblox_app")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

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

# Include routers
app.include_router(router)
app.include_router(dashboard_router)

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
    logger.info("Starting Roblox API server...")

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

