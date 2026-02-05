"""
FastAPI application main file.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import surveys, answer_options
from .models import Base, engine

app = FastAPI(
    title="Survey Analytics API",
    description="API for managing and analyzing survey data",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv(
    "CORS_ORIGINS",
    (
        "http://localhost:5173,http://localhost:3000,"
        "http://localhost:8080,http://localhost"
    ),
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables exist on startup."""
    Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(surveys.router)
app.include_router(answer_options.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Survey Analytics API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
