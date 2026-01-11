from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from app.core.config import settings

load_dotenv()

app = FastAPI(title="Vellum Chatbot API", description="Backend for Vellum Enterprise Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.api import api_router

from fastapi.staticfiles import StaticFiles

# Create data/source_documents if not exists (for Docker volume)
os.makedirs("data/source_documents", exist_ok=True)

# Mount files
app.mount("/api/v1/files", StaticFiles(directory="data/source_documents"), name="files")

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Vellum API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
