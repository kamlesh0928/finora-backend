import os
import json
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, close_db
from .routes import auth, user, wallet, game, fraud, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=os.getenv("APP_NAME", "Finora API"),
    description="Backend API for Finora — Gamified Financial Literacy for Bharat",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
cors_origins_str = os.getenv("CORS_ORIGINS", '["*"]')
try:
    cors_origins = json.loads(cors_origins_str)
except json.JSONDecodeError:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
api_prefix = os.getenv("API_PREFIX", "/api")
app.include_router(auth.router, prefix=api_prefix)
app.include_router(user.router, prefix=api_prefix)
app.include_router(wallet.router, prefix=api_prefix)
app.include_router(game.router, prefix=api_prefix)
app.include_router(fraud.router, prefix=api_prefix)
app.include_router(sync.router, prefix=api_prefix)


# Health Check Endpoints
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "app": os.getenv("APP_NAME", "Finora API"),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development").lower() != "production",
        log_level="info"
    )