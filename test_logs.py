import httpx
import random
from datetime import datetime, timezone

# ------------------ CONFIG ------------------
API_URL = "http://127.0.0.1:8000/logs"  # FastAPI logs endpoint
API_KEY = "supersecretapikey"           # Must match settings.API_KEY
HEADERS = {"X-API-Key": API_KEY}

# ------------------ LOG TEMPLATES ------------------
normal_log_template = {
    "hostname": "DESKTOP-TEST",
    "cpu_usage": 20,
    "total_memory": 16000,
    "used_memory": 4000,
    "disk_io": 100,
    "processes": ["explorer.exe", "svchost.exe", "python.exe"],
    "network_sent": 10,
    "network_transmitted": 10,
    "network_received": 15,
}

anomalous_log_template = {
    "hostname": "DESKTOP-TEST",
    "cpu_usage": 99,
    "total_memory": 16000,
    "used_memory": 15900,
    "disk_io": 3000,
    "processes": ["malware.exe", "cryptominer.exe", "suspicious.exe"],
    "network_sent": 2000,
    "network_transmitted": 2000,
    "network_received": 2000,
}

# ------------------ FUNCTION TO CREATE LOG ------------------
def create_log(anomalous=False):
    log = normal_log_template.copy()
    if anomalous:
        # Exaggerate all numerical features to trigger anomaly detection
        log.update({
            "cpu_usage": random.randint(95, 100),
            "used_memory": random.randint(15000, 16000),
            "disk_io": random.randint(2000, 3000),
            "processes": [f"suspicious_process_{i}.exe" for i in range(random.randint(3, 6))],
            "network_sent": random.randint(1000, 2000),
            "network_transmitted": random.randint(1000, 2000),
            "network_received": random.randint(1000, 2000),
        })
    log["timestamp"] = datetime.now(timezone.utc).isoformat()
    return log

# ------------------ GENERATE LOGS ------------------
logs = []
for i in range(10):
    # Force every 3rd log to be anomalous
    logs.append(create_log(anomalous=(i % 3 == 0)))

# ------------------ SEND LOGS TO FASTAPI ------------------
try:
    response = httpx.post(API_URL, json=logs, headers=HEADERS)
    print("API Response:", response.status_code, response.json())
except Exception as e:
    print("Failed to send logs:", e)
