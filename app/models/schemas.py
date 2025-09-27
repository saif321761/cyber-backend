# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class LogItem(BaseModel):
    hostname: str
    processes: List[str]
    total_memory: int
    used_memory: int
    network_received: int
    network_transmitted: int

class LogsIn(BaseModel):
    logs: List[LogItem]

class AlertIn(BaseModel):
    title: str
    level: Optional[str] = "info"  # info|warning|critical
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    related_logs: Optional[List[LogItem]] = None
