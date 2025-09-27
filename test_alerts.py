import httpx
from datetime import datetime

url = "http://127.0.0.1:8000/alerts"  # FastAPI running locally
headers = {
    "X-API-Key": "supersecretapikey",
    "Content-Type": "application/json"
}

payload = {
    "title": "Test Alert",
    "level": "info",
    "message": "This is a test alert",
    "timestamp": datetime.utcnow().isoformat(),  # ✅ proper ISO format
    "related_logs": [
        {
            "hostname": "DESKTOP-CHBR0NO",
            "processes": ["python.exe", "chrome.exe", "Code.exe"],
            "total_memory": 17015463936,
            "used_memory": 11663278080,
            "network_received": 321,
            "network_transmitted": 54
        }
    ]
}

response = httpx.post(url, json=payload, headers=headers)
print("Status code:", response.status_code)
print("Response:", response.json())
