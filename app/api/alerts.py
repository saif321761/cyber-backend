# app/api/alerts.py
from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.models.schemas import AlertIn
from app.services.n8n_client import post_to_n8n
from app.core.config import settings
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.models.device import Device

# Firebase imports
import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
from datetime import datetime
import json

router = APIRouter(prefix="", tags=["alerts"])

# ------------------------ Firebase Init ------------------------
if not firebase_admin._apps:
    cred_path = Path("C:/Users/Al Shahbaz/Desktop/Cyber-backend/serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized")


# ------------------------ API key check ------------------------
def check_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key


# ------------------------ Helper: make datetime serializable ------------------------
def to_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


# ------------------------ Helper: send push to multiple devices ------------------------
def send_push_to_devices(tokens: list[str], title: str, body: str, data: dict = None):
    """Send push notification to multiple device tokens."""
    
    if not tokens:
        print("⚠️ No device tokens to send push notifications.")
        return None

    # Method 1: Try using send_multicast if available (newer SDK versions)
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
            data=data or {}
        )
        response = messaging.send_multicast(message)
        print(f"📲 Firebase push result: {response.success_count} sent, {response.failure_count} failed")

        for idx, resp in enumerate(response.responses):
            if not resp.success:
                print(f"❌ Failed token: {tokens[idx]}, error: {resp.exception}")

        return response
        
    except AttributeError:
        # Method 2: Fallback to individual sends (older SDK versions)
        print("ℹ️ Multicast not available, sending individual messages")
        success_count = 0
        failure_count = 0
        
        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    token=token,
                    data=data or {}
                )
                response = messaging.send(message)
                success_count += 1
                print(f"✅ Sent to token: {token[:10]}...")
            except Exception as e:
                failure_count += 1
                print(f"❌ Failed to send to token {token[:10]}...: {e}")
        
        # Create a simple response object to match the expected structure
        class SimpleResponse:
            def __init__(self, success, failures):
                self.success_count = success
                self.failure_count = failures
                self.responses = []
        
        return SimpleResponse(success_count, failure_count)


# ------------------------ POST /alerts ------------------------
@router.post("/alerts")
async def push_alert(
    alert: AlertIn,
    db: Session = Depends(get_db),
    x_api_key: str = Depends(check_api_key)
):
    # 1️⃣ Send to n8n
    payload = {"source": "backend_manual", "alert": alert.dict()}
    payload = json.loads(json.dumps(payload, default=to_serializable))
    try:
        n8n_res = await post_to_n8n(payload)
        print("n8n response:", n8n_res)
    except Exception as e:
        print(f"❌ Failed to send alert to n8n: {e}")
        n8n_res = {"ok": False, "error": str(e)}

    # 2️⃣ Fetch device tokens
    tokens = [t[0] for t in db.query(Device.fcm_token).all()]
    print("📱 Device tokens:", tokens)

    # 3️⃣ Send push notifications
    push_response = None
    if tokens:
        push_response = send_push_to_devices(
            tokens=tokens,
            title=f"🚨 {alert.title}",
            body=alert.message,
            data={"alert_id": str(getattr(alert, "id", ""))}
        )

    return {
        "ok": True,
        "n8n": n8n_res,
        "push": {
            "success_count": push_response.success_count if push_response else 0,
            "failure_count": push_response.failure_count if push_response else 0,
        }
    }