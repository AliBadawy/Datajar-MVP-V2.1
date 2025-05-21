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
# Much simpler approach to ensure CORS headers are always applied
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteMiddleware

# Force direct CORS headers for Netlify domains
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "https://delightful-zabaione-7c09dd.netlify.app"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    
    # Log that we're adding headers manually
    logger.info(f"Added manual CORS headers to response")
    return response

# Still add the middleware as a backup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://delightful-zabaione-7c09dd.netlify.app",
        "https://datajar-mvp-v21.netlify.app",
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured with direct header injection for primary domain")

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
