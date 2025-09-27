# app/routers/devices.py
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.db import get_db
from app.models.device import Device

router = APIRouter(prefix="/devices", tags=["devices"])

# ------------------------
# API key check (reuse from alerts.py)
# ------------------------
def check_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

# ------------------------
# Pydantic schema for registering a device
# ------------------------
class DeviceTokenIn(BaseModel):
    fcm_token: str   # ✅ only token, no user_id

# ------------------------
# Endpoint to register device tokens
# ------------------------
# Remove the header check
@router.post("/register")
async def register_device(
    device: DeviceTokenIn,
    db: Session = Depends(get_db),
):
    # Check if device already exists
    existing = db.query(Device).filter(Device.fcm_token == device.fcm_token).first()
    if existing:
        # Device token already registered
        return {"ok": True, "message": "Device token already registered"}

    # Create new device token
    new_device = Device(fcm_token=device.fcm_token)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return {
        "ok": True,
        "message": "Device token stored",
        "device": {
            "fcm_token": new_device.fcm_token,
            "created_at": new_device.created_at
        }
    }


