# app/utils/preprocessing.py
from typing import List, Dict, Any
import numpy as np

def event_type_hash_normalized(event_type: str) -> float:
    if not event_type:
        return 0.0
    return (abs(hash(event_type)) % 1000) / 1000.0

def ip_sum_octets(ip: str) -> int:
    if not ip:
        return 0
    try:
        parts = ip.split('.')
        return sum(int(p) for p in parts[:4])
    except Exception:
        return 0

def extract_features(log: Dict[str, Any]) -> List[float]:
    """MVP feature extractor: returns fixed-length numeric vector per log."""
    request_size = int(log.get("request_size") or 0)
    latency_ms = float(log.get("latency_ms") or 0.0)
    response_code = int(log.get("response_code") or 0)
    ua_len = len(str(log.get("user_agent") or ""))
    metadata_len = len(log.get("metadata") or {})
    evt_hash = event_type_hash_normalized(log.get("event_type") or "")
    ip_sum = ip_sum_octets(log.get("ip") or "")
    # Order: [request_size, latency_ms, response_code, ua_len, metadata_len, evt_hash, ip_sum]
    return [request_size, latency_ms, response_code, ua_len, metadata_len, evt_hash, ip_sum]

def batch_to_matrix(batch: List[Dict]) -> "np.ndarray":
    import numpy as np
    rows = [extract_features(l) for l in batch]
    return np.array(rows, dtype=float)
