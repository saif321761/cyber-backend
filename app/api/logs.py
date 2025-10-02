from fastapi import APIRouter, Request, Depends, Header, HTTPException, status
from typing import Optional, List
from app.models.schemas import LogItem
from fastapi.responses import JSONResponse
from app.services.detector import AnomalyDetector
from app.services.n8n_client import post_to_n8n
from app.utils.preprocessing import batch_to_matrix
from app.core.config import settings
from fastapi.concurrency import run_in_threadpool
from datetime import datetime
from httpx import AsyncClient
import asyncio

router = APIRouter(prefix="/logs", tags=["logs"])

# ----------------- GLOBAL VARIABLES -----------------
detector: AnomalyDetector | None = None
log_buffer: List[dict] = []  # Buffer to accumulate logs
MAX_BUFFER_SIZE = 1000
MIN_LOGS_FOR_TRAINING = 5

# ----------------- API KEY CHECK -----------------
def check_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return x_api_key

# ----------------- DETECTOR INIT -----------------
@router.on_event("startup")
async def init_detector():
    """Initialize detector on startup"""
    global detector
    detector = AnomalyDetector()
    print("✅ Detector initialized (waiting for logs to train)")

# ----------------- PROCESS & FORWARD -----------------
async def _process_and_forward(logs: list):
    global detector, log_buffer
    
    # Add new logs to buffer
    log_buffer.extend(logs)
    
    # Keep buffer size manageable
    if len(log_buffer) > MAX_BUFFER_SIZE:
        log_buffer = log_buffer[-MAX_BUFFER_SIZE:]
    
    print(f"📊 Log buffer size: {len(log_buffer)}")
    
    results = []

    if detector is not None:
        try:
            # Train model if we have enough logs and it's not trained yet
            if not detector.trained and len(log_buffer) >= MIN_LOGS_FOR_TRAINING:
                print(f"🎯 Training model with {len(log_buffer)} accumulated logs...")
                await run_in_threadpool(detector.fit, log_buffer)
            
            # Use the detector's predict method
            detection_results = await run_in_threadpool(detector.predict, logs)
            results = detection_results
                    
        except Exception as e:
            print("❌ Prediction failed:", e)
            # Fallback: create default results
            for log in logs:
                log_serialized = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in log.items()}
                results.append({
                    "log": log_serialized,
                    "is_anomaly": False,
                    "score": 0.0,
                })
    else:
        # Fallback if detector not initialized
        for log in logs:
            log_serialized = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in log.items()}
            results.append({
                "log": log_serialized,
                "is_anomaly": False,
                "score": 0.0,
            })

    # Auto-generate alert if anomaly
    for result in results:
        is_anomaly = result["is_anomaly"]
        
        if is_anomaly:
            alert_payload = {
                "title": "Anomaly detected",
                "level": "warning",
                "message": f"Suspicious activity on device {result['log'].get('hostname')}",
                "timestamp": datetime.utcnow().isoformat(),
                "related_logs": [result['log']],
            }

            LOCAL_IP = "192.168.18.54"
            ALERTS_URL = f"http://{LOCAL_IP}:8000/alerts"

            try:
                async with AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        ALERTS_URL,
                        headers={"X-API-Key": settings.API_KEY},
                        json=alert_payload,
                    )
                if response.status_code in (200, 202):
                    print(f"🚨 Alert sent for anomaly on {result['log'].get('hostname')}")
                else:
                    print(f"⚠️ Alert endpoint returned status: {response.status_code}")
            except Exception as e:
                print(f"💥 Could not send alert: {e}")

    # Send all logs to n8n
    try:
        serializable_results = []
        for result in results:
            serializable_result = {
                "log": result["log"],
                "is_anomaly": bool(result["is_anomaly"]),
                "score": float(result["score"])
            }
            serializable_results.append(serializable_result)
        
        payload = {"source": "backend_detection", "results": serializable_results}
        n8n_resp = await post_to_n8n(payload)
        print("📤 n8n response:", n8n_resp)
    except Exception as e:
        print("❌ Failed to send logs to n8n:", e)
        n8n_resp = {"ok": False, "error": str(e)}

    return {"ok": True, "detected": sum(1 for r in results if r["is_anomaly"]), "n8n": n8n_resp}

# ----------------- RECEIVE LOGS -----------------
@router.post("", status_code=202)
async def receive_logs(request: Request, x_api_key: str = Depends(check_api_key)):
    body = await request.json()
    raw_logs = body if isinstance(body, list) else (
        body.get("logs") if isinstance(body, dict) and "logs" in body else [body]
    )

    validated = []
    for r in raw_logs:
        try:
            li = LogItem.parse_obj(r)
            validated.append(li.dict())
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid log item: {e}")

    # Run processing in background
    asyncio.create_task(_process_and_forward(validated))

    return JSONResponse(
        status_code=202,
        content={
            "accepted": len(validated), 
            "message": "Logs accepted and being processed.",
            "buffer_size": len(log_buffer),
            "model_trained": detector.trained if detector else False
        }
    )

# ----------------- STATUS ENDPOINT -----------------
@router.get("/status")
async def get_status():
    """Get current detector status"""
    return {
        "model_trained": detector.trained if detector else False,
        "logs_in_buffer": len(log_buffer),
        "min_logs_for_training": MIN_LOGS_FOR_TRAINING,
        "status": "ready" if detector and detector.trained else "waiting_for_data"
    }