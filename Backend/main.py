# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# Configure CORS to allow communication with frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178", "http://localhost:5179", "http://localhost:5180", "http://localhost:5181", "http://localhost:5182", "http://localhost:5183", "http://localhost:5184"],  # frontend URLs including Vite's default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
