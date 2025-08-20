from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.core.scheduler import scheduler
from app.routers import trades, strategy, analytics, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VIX/SPY Trading Dashboard")
    scheduler.start()
    logger.info("Background scheduler started")
    yield
    logger.info("Shutting down VIX/SPY Trading Dashboard")
    scheduler.shutdown(wait=False)
    logger.info("Background scheduler stopped")

app = FastAPI(
    title="VIX/SPY Iron Condor Trading Dashboard",
    description="Automated trading dashboard for VIX/SPY iron condor strategy",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["strategy"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(health.router, prefix="/api/health", tags=["health"])

@app.get("/")
async def root():
    return {
        "message": "VIX/SPY Iron Condor Trading Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )