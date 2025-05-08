# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routers.analyze_router import router as analyze_router
from routers.project_router import router as project_router
from routers.message_router import router as message_router
from routers.salla_auth_router import router as salla_auth_router
from routers.salla_router import router as salla_router

# Initialize FastAPI app
app = FastAPI()

# Configure CORS to allow communication with frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
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
        "http://127.0.0.1:65325",  # Add this line specifically for your current browser preview
        "*",  # This will allow all origins - use only in development!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze_router)
app.include_router(project_router)
app.include_router(message_router)
app.include_router(salla_auth_router)
app.include_router(salla_router)

# Define request schema
class ChatMessage(BaseModel):
    content: str

# Define echo endpoint
@app.post("/api/chat")
async def chat(message: ChatMessage):
    return {"response": f"Echo: {message.content}"}

# Add a health check endpoint
@app.get("/")
async def health_check():
    return {"status": "Backend server is running"}
