# app/main.py
from fastapi import FastAPI
from app.api import logs, alerts, devices
from app.services.detector import AnomalyDetector
from app.core.config import settings
from app.core.db import Base, engine  # import Base and engine

app = FastAPI(title="Cyber-Backend", version="0.1.0")

# mount routers
app.include_router(logs.router)
app.include_router(alerts.router)
app.include_router(devices.router)

@app.on_event("startup")
async def startup_event():
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Instantiate detector
    global global_detector
    global_detector = AnomalyDetector()

    # attach to logs module so router uses same instance
    import app.api.logs as logs_module
    logs_module.detector = global_detector

@app.get("/health")
async def health():
    return {
        "ok": True,
        "model_trained": global_detector.is_trained() if "global_detector" in globals() else False
    }
