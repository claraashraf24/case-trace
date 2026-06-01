from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import Case, Evidence, Event


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Incident Reconstruction & Intelligence Platform",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "CaseTrace AI backend is running",
        "status": "ok",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_prefix": "/api/v1",
    }


app.include_router(api_router, prefix="/api/v1")