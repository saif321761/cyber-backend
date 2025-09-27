from fastapi import APIRouter, Request, Depends, Header, HTTPException, status
from typing import Optional
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

# ----------------- API KEY CHECK -----------------
def check_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return x_api_key

# ----------------- DETECTOR -----------------
detector: AnomalyDetector | None = None

@router.on_event("startup")
async def init_detector():
    """Initialize detector on startup"""
    global detector
    detector = AnomalyDetector()
    print("Detector initialized (untrained until first fit)")

# ----------------- PROCESS & FORWARD -----------------
async def _process_and_forward(logs: list):
    global detector
    results = []

    if detector is not None:
        X = batch_to_matrix(logs)
        try:
            preds, scores = await run_in_threadpool(detector.predict, X)
        except Exception as e:
            print("Prediction failed:", e)
            preds = [1] * len(logs)
            scores = [0.0] * len(logs)
    else:
        preds = [1] * len(logs)
        scores = [0.0] * len(logs)

    for i, log in enumerate(logs):
        log_serialized = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in log.items()}
        is_anomaly = bool(preds[i] == -1)

        results.append({
            "log": log_serialized,
            "is_anomaly": is_anomaly,
            "score": float(scores[i]),
        })
        # is_anomaly = True
        # Auto-generate alert if anomaly
        if is_anomaly:
            alert_payload = {
                "title": "Anomaly detected",
                "level": "warning",
                "message": f"Suspicious activity on device {log.get('hostname')}",
                "timestamp": datetime.utcnow().isoformat(),
                "related_logs": [log_serialized],
            }

            LOCAL_IP = "192.168.18.54"
            ALERTS_URL = f"http://{LOCAL_IP}:8000/alerts"

            try:
                async with AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        ALERTS_URL,
                        headers={"X-API-Key": settings.API_KEY},
                        json=alert_payload,
                    )
                if response.status_code in (200, 202):
                    print(f"Alert sent for anomaly on {log.get('hostname')}")
                    print("Response from /alerts:", response.text)
                else:
                    print(f"Failed to send alert. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Exception while sending alert for {log.get('hostname')}: {e}")

    # Send all logs to n8n
    payload = {"source": "backend_detection", "results": results}
    try:
        n8n_resp = await post_to_n8n(payload)
        print("n8n response:", n8n_resp)
    except Exception as e:
        print("Failed to send logs to n8n:", e)
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
        content={"accepted": len(validated), "message": "Logs accepted and being processed."}
    )
