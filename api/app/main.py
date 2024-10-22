from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Now the environment variable OPENAI_API_KEY will be available via os.getenv
openai_api_key = os.getenv("OPENAI_API_KEY")
from app.routers import router  # Import the router from routers.py
import logging

# Define log format and level
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define log format
)

logger = logging.getLogger("roblox_app")
logger.setLevel(logging.DEBUG)  # Ensure that this logger captures DEBUG-level logs

# Create FastAPI app
app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include router
app.include_router(router)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="."), name="static")

# Serve the dashboard.html file
@app.get("/")
async def serve_dashboard():
    return FileResponse("dashboard.html")

# Optionally add startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("RobloxAPI app is starting...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RobloxAPI app is shutting down...")
