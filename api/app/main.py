import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import logging

# Load environment variables from .env
load_dotenv()

# Now the environment variable OPENAI_API_KEY will be available via os.getenv
openai_api_key = os.getenv("OPENAI_API_KEY")
from app.routers import router  # Import the main router
from app.dashboard_router import router as dashboard_router  # Import the dashboard router

# Define log format and level
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("roblox_app")
logger.setLevel(logging.DEBUG)

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

# Include routers - note that we're not adding a prefix to the dashboard router
app.include_router(router)
app.include_router(dashboard_router)  # Remove the prefix so endpoints are at root level

# Calculate absolute paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This gets us to the api/ directory
static_directory = os.path.join(current_dir, "static")

# Mount the static files directory
app.mount("/static", StaticFiles(directory=static_directory), name="static")

# Serve HTML files
@app.get("/")
@app.get("/dashboard")
async def serve_dashboard():
    dashboard_path = os.path.join(current_dir, "dashboard.html")
    logger.info(f"Serving dashboard from: {dashboard_path}")
    return FileResponse(dashboard_path)

@app.get("/npcs")
async def serve_npcs():
    npcs_path = os.path.join(current_dir, "npcs.html")
    logger.info(f"Serving NPCs from: {npcs_path}")
    return FileResponse(npcs_path)

@app.get("/players")
async def serve_players():
    players_path = os.path.join(current_dir, "players.html")
    logger.info(f"Serving players from: {players_path}")
    return FileResponse(players_path)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("RobloxAPI app is starting...")
    logger.info(f"Current directory: {current_dir}")
    logger.info(f"Static directory: {static_directory}")
    logger.info(f"Dashboard path: {os.path.join(current_dir, 'dashboard.html')}")
    logger.info(f"NPCs path: {os.path.join(current_dir, 'npcs.html')}")
    logger.info(f"Players path: {os.path.join(current_dir, 'players.html')}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RobloxAPI app is shutting down...")
