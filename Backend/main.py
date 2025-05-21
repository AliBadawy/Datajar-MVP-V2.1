# main.py
import logging
import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add health check endpoint immediately
@app.get("/health")
def health_check():
    """Health check endpoint that doesn't depend on other imports"""
    return {"status": "ok", "message": "API is running"}

# Import traceback for detailed error reporting
import traceback

# Import routers after setting up basic app functionality
# This helps avoid crashing the entire app if there's an import error
try:
    from routers.analyze_router import router as analyze_router
    from routers.project_router import router as project_router
    from routers.message_router import router as message_router
    from routers.salla_auth_router import router as salla_auth_router
    from routers.salla_router import router as salla_router
    logger.info("Successfully imported all routers")
except Exception as e:
    logger.error(f"Error importing routers: {str(e)}")
    logger.error("Full traceback:")
    logger.error(traceback.format_exc())
    # Continue app startup even if router imports fail

# Configure CORS to allow communication with frontend
# When using credentials=True, we need to explicitly list all origins
# The wildcard "*" doesn't work with credentials
production_domains = [
    "https://delightful-zabaione-7c09dd.netlify.app",
    "https://datajar-mvp-v21.netlify.app",
    # Add any additional domains here
]

local_dev_domains = [
    "http://localhost:3000", 
    "http://localhost:5173", 
    "http://localhost:5174", 
    "http://localhost:5175", 
    "http://localhost:5176", 
    "http://localhost:5177", 
    "http://localhost:5178", 
    "http://localhost:5179", 
    "http://localhost:5180", 
    "http://localhost:5181", 
    "http://localhost:5182", 
    "http://localhost:5183", 
    "http://localhost:5184",
    "http://localhost:5185",
    "http://127.0.0.1:5185",
    "http://127.0.0.1:65325",
]

# Use environment variable to control CORS settings
debug_mode = os.getenv("DEBUG_MODE", "False").lower() == "true"

if debug_mode:
    # In debug mode, accept all origins but don't use credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Set to False when using wildcard
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.warning("Running in debug mode with permissive CORS settings")
else:
    # In production mode, list specific origins with credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=production_domains + local_dev_domains,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS configured for {len(production_domains)} production domains")

# Include routers if they were successfully imported
try:
    # These variables will exist only if the imports succeeded
    if 'analyze_router' in locals():
        app.include_router(analyze_router)
        logger.info("Included analyze_router")
    
    if 'project_router' in locals():
        app.include_router(project_router, prefix="/api")
        logger.info("Included project_router with prefix /api")
    
    if 'message_router' in locals():
        app.include_router(message_router)
        logger.info("Included message_router")
    
    if 'salla_auth_router' in locals():
        app.include_router(salla_auth_router)
        logger.info("Included salla_auth_router")
    
    if 'salla_router' in locals():
        app.include_router(salla_router)
        logger.info("Included salla_router")
except Exception as e:
    logger.error(f"Error including routers: {str(e)}")
    logger.error("Full traceback:")
    logger.error(traceback.format_exc())

# Define request schema
class ChatMessage(BaseModel):
    content: str

# Define echo endpoint
@app.post("/api/chat")
async def chat(message: ChatMessage):
    return {"response": f"Echo: {message.content}"}

# Add health check endpoints
@app.get("/")
async def root():
    return {"status": "Backend server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "datajar-backend"}
