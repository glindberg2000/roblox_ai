from fastapi import FastAPI
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

# Include router
app.include_router(router)

# Optionally add startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("RobloxAPI app is starting...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RobloxAPI app is shutting down...")