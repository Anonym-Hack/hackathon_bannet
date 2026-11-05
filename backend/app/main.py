import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import UPLOAD_DIR, GEMINI_API_KEY, GEMINI_MODEL
from app.database import engine, Base, SessionLocal
from app.seed_data import seed_database_if_empty

from app.routers import (
    auth,
    listings,
    requests,
    matches,
    inquiries,
    analytics,
    ai
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("resource_ai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables created and seed data loaded
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
    finally:
        db.close()
    
    logger.info("ReSource AI Backend initialized successfully.")
    yield
    # Shutdown
    logger.info("ReSource AI Backend shutting down.")

app = FastAPI(
    title="ReSource AI API",
    description="Intelligent Circular Economy & Industrial Waste Exchange Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images statically
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include Routers under /api
api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(listings.router, prefix=api_prefix)
app.include_router(requests.router, prefix=api_prefix)
app.include_router(matches.router, prefix=api_prefix)
app.include_router(inquiries.router, prefix=api_prefix)
app.include_router(analytics.router, prefix=api_prefix)
app.include_router(ai.router, prefix=api_prefix)

@app.get("/")
def root():
    return {
        "app": "ReSource AI",
        "description": "AI-Powered Industrial Waste & Material Circular Marketplace",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "gemini_api_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL if GEMINI_API_KEY else "demo_rule_based"
    }

@app.get("/api")
def api_status():
    return {
        "status": "healthy",
        "service": "resource-ai-api",
        "demo_ai_fallback": True,
        "has_gemini_key": bool(GEMINI_API_KEY)
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."}
    )
