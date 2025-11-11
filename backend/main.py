# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import rag_router # Import the new router

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Document Intelligent Hub - Multi-Tenant RAG System."
)

# --- CORS Configuration ---
# CORS is required to allow the React frontend (running on a different port/origin) 
# to communicate with this FastAPI backend.
origins = [
    # Allow all origins for development (usually 'http://localhost:3000' or similar)
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- Router Registration ---
# Register the RAG API endpoints
app.include_router(rag_router.router)

# --- Root Endpoint (Health Check) ---
@app.get("/")
def read_root():
    return {"message": f"{settings.PROJECT_NAME} API is running!"}

# --- IMPORTANT: Setup Persistence Folders ---
# This ensures that the ChromaDB data folder is created on startup.
import os  # noqa: E402
if not os.path.exists(settings.CHROMA_DB_PATH):
    os.makedirs(settings.CHROMA_DB_PATH)
    print(f"Created persistent database folder: {settings.CHROMA_DB_PATH}")