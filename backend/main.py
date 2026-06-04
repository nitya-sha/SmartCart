"""
SmartCart API — main entry point.
Run with: uvicorn main:app --reload
API docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.v1 import router as v1_router

app = FastAPI(
    title="SmartCart API",
    description="AI-powered E-Commerce Analytics & Recommendation Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow React dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "SmartCart API is running!",
        "docs": "/docs",
        "version": "1.0.0",
    }