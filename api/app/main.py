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

# Route handlers
@app.get("/")
@app.get("/dashboard")
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/npcs")
async def serve_npcs():
    npcs_path = TEMPLATES_DIR / "npcs.html"
    if not npcs_path.exists():
        logger.error(f"NPCs file not found at {npcs_path}")
        raise HTTPException(status_code=404, detail=f"NPCs file not found")
    return FileResponse(str(npcs_path))

@app.get("/players")
async def serve_players():
    players_path = TEMPLATES_DIR / "players.html"
    if not players_path.exists():
        logger.error(f"Players file not found at {players_path}")
        raise HTTPException(status_code=404, detail=f"Players file not found")
    return FileResponse(str(players_path))

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

