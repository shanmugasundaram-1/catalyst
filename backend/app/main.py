from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, ensure_schema_compatibility
from app.services.scheduler_service import start_scheduler, stop_scheduler

from app.routers import (
    auth,
    profiles,
    medications,
    doses,
    appointments,
    approvals,
    activity,
    ai,
    sos,
    voice,
    insights
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables and ensure schema compatibility
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    # Auto-seed demo data on startup if not present
    try:
        from app.core.database import SessionLocal
        from app.models import Profile
        db = SessionLocal()
        try:
            exists = db.query(Profile).filter(Profile.id == "DEMO-ELDER").first()
            if not exists:
                import sys, os
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), "..", "seed_data.py"),
                    os.path.join(os.getcwd(), "backend", "seed_data.py"),
                    os.path.join(os.getcwd(), "seed_data.py")
                ]
                for sp in possible_paths:
                    if os.path.exists(sp):
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("seed_module", sp)
                        seed_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(seed_mod)
                        if hasattr(seed_mod, "seed"):
                            seed_mod.seed()
                        elif hasattr(seed_mod, "seed_demo_data"):
                            seed_mod.seed_demo_data()
                        break
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger("ayucare").warning(f"Auto-seed exception: {e}")
    # Start background scheduler
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title="AyuCare API",
    description="Elderly Care & Medication Management Platform - Google Build with AI Hackathon",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
# In development FRONTEND_URL is http://localhost:5173; in production restrict origins explicitly
_cors_origins = list({
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    settings.FRONTEND_URL,
    # Vercel deployment patterns
    "https://ayucare-catalyst.vercel.app",
    "https://catalyst-shanmugasundaram-1.vercel.app",
})
# Only allow wildcard in development; never in production
if settings.APP_ENV == "development":
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=settings.APP_ENV != "development",  # credentials+wildcard disallowed by browsers
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(medications.router)
app.include_router(doses.router)
app.include_router(appointments.router)
app.include_router(approvals.router)
app.include_router(activity.router)
app.include_router(ai.router)
app.include_router(sos.router)
app.include_router(voice.router)
app.include_router(insights.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AyuCare Platform",
        "environment": settings.APP_ENV,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
