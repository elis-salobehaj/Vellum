from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging

# Initialize Logging
setup_logging()

load_dotenv()

app = FastAPI(title="Vellum Chatbot API", description="Backend for Vellum Enterprise Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:9090",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core API routes from api_router
# We include them twice: once at root for legacy/direct access (e.g., /health, /files)
# and once with the Version 1 prefix (e.g., /api/v1/health)
app.include_router(api_router)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Vellum API"}
