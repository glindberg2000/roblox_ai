import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import logging
from .db import init_db

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("roblox_app")
logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Setup paths
BASE_DIR = Path(os.getcwd())  # This will be /home/plato/dev/roblox/api
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR

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
from routers import router
from routers.dashboard_router import router as dashboard_router
from routers import v4, letta_router  # Add the Letta router import

# Include routers
app.include_router(router)
app.include_router(dashboard_router)
app.include_router(v4.router)
app.include_router(letta_router.router)  # Include the Letta router

# Create static directory if it doesn't exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Route handlers
@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    dashboard_path = TEMPLATES_DIR / "dashboard.html"
    logger.info(f"Serving dashboard from: {dashboard_path}")
    if not dashboard_path.exists():
        logger.error(f"Dashboard file not found at {dashboard_path}")
        raise HTTPException(status_code=404, detail=f"Dashboard file not found at {dashboard_path}")
    return FileResponse(str(dashboard_path))

@app.get("/npcs")
async def serve_npcs():
    npcs_path = TEMPLATES_DIR / "npcs.html"
    logger.info(f"Serving NPCs from: {npcs_path}")
    if not npcs_path.exists():
        logger.error(f"NPCs file not found at {npcs_path}")
        raise HTTPException(status_code=404, detail=f"NPCs file not found at {npcs_path}")
    return FileResponse(str(npcs_path))

@app.get("/players")
async def serve_players():
    players_path = TEMPLATES_DIR / "players.html"
    logger.info(f"Serving players from: {players_path}")
    if not players_path.exists():
        logger.error(f"Players file not found at {players_path}")
        raise HTTPException(status_code=404, detail=f"Players file not found at {players_path}")
    return FileResponse(str(players_path))

@app.on_event("startup")
async def startup_event():
    logger.info("RobloxAPI app is starting...")
    logger.info(f"Current directory: {BASE_DIR}")
    logger.info(f"Static directory: {STATIC_DIR}")
    logger.info(f"Templates directory: {TEMPLATES_DIR}")
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RobloxAPI app is shutting down...")

@app.get("/static/js/dashboard.js")
async def serve_dashboard_js():
    js_path = STATIC_DIR / "js" / "dashboard.js"
    logger.info(f"Serving dashboard.js from: {js_path}")
    if not js_path.exists():
        logger.error(f"dashboard.js not found at {js_path}")
        raise HTTPException(status_code=404, detail=f"dashboard.js not found at {js_path}")
    return FileResponse(str(js_path), media_type="application/javascript") 