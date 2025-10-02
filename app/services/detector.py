from sklearn.ensemble import IsolationForest
import numpy as np
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            max_samples='auto'
        )
        self.trained = False
        self.feature_names = []
        print(f"✅ AnomalyDetector initialized with contamination={contamination}")

    def _to_features(self, logs: List[dict]) -> np.ndarray:
        """Convert list of log dicts into numeric feature matrix"""
        print(f"🔧 Converting {len(logs)} logs to features...")
        rows = []
        
        for i, log in enumerate(logs):
            # Extract and calculate features
            total_mem = log.get("total_memory", 1)
            used_mem = log.get("used_memory", 0)
            
            # 1. Memory usage percentage (most important)
            memory_usage_pct = (used_mem / total_mem) * 100 if total_mem > 0 else 0
            
            # 2. Process count (important for detection)
            process_count = len(log.get("processes", []))
            
            # 3. Network activity (combined)
            network_activity = log.get("network_received", 0) + log.get("network_transmitted", 0)
            
            # 4. CPU usage (if available)
            cpu_usage = log.get("cpu_usage", 0)
            
            # 5. Disk I/O (if available)
            disk_io = log.get("disk_io", 0)
            
            # Create feature vector
            row = [
                memory_usage_pct,
                process_count,
                np.log1p(network_activity),
                cpu_usage,
                np.log1p(disk_io),
                used_mem / (1024**3),
            ]
            rows.append(row)
            
            if i == 0:
                print(f"📊 Sample features - Memory: {memory_usage_pct:.1f}%, Processes: {process_count}, CPU: {cpu_usage:.1f}%")
        
        self.feature_names = ["memory_pct", "process_count", "network_log", "cpu_usage", "disk_io_log", "memory_gb"]
        X = np.array(rows, dtype=float)
        
        print(f"📈 Feature matrix shape: {X.shape}")
        return X

    def fit(self, logs: List[dict]):
        """Train the model on normal data"""
        if len(logs) == 0:
            print("❌ No logs provided for training")
            return False
            
        print(f"🎯 Training model with {len(logs)} samples...")
        
        if len(logs) < 5:
            print(f"⚠️  Need at least 5 logs for training, got {len(logs)}")
            return False
        
        try:
            X = self._to_features(logs)
            self.model.fit(X)
            self.trained = True
            print(f"✅ Model trained on {len(logs)} samples")
            return True
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False

    def predict(self, logs):
        """Predict anomalies in logs"""
        if len(logs) == 0:
            return []
            
        print(f"🔍 Predicting anomalies for {len(logs)} logs...")
        
        # Handle different input types
        if isinstance(logs, list) and isinstance(logs[0], dict):
            print("📥 Input type: List of dicts")
            X = self._to_features(logs)
            return_dicts = True
        else:
            raise ValueError("predict() expects a list of dicts")

        # If model not trained, use simple rule-based detection
        if not self.trained:
            print("⚠️  Model not trained yet. Using rule-based detection.")
            return self._rule_based_detection(logs)

        # Get predictions and scores
        preds = self.model.predict(X)
        scores = self.model.decision_function(X)
        
        anomaly_count = sum(preds == -1)
        print(f"📊 Predictions: {anomaly_count} anomalies out of {len(preds)} samples")
        
        # Apply adaptive threshold
        threshold = -0.02
        for i, score in enumerate(scores):
            if score < threshold:
                preds[i] = -1
            elif score > 0.1:
                preds[i] = 1

        # Return results
        results = []
        for i, (log, pred, score) in enumerate(zip(logs, preds, scores)):
            results.append({
                "log": log,
                "is_anomaly": bool(pred == -1),
                "score": float(score)
            })
            
            if pred == -1:
                mem_pct = (log.get("used_memory", 0) / log.get("total_memory", 1)) * 100
                print(f"🚨 ANOMALY DETECTED: Memory: {mem_pct:.1f}%, Processes: {len(log.get('processes', []))}, Score: {score:.3f}")
                    
        return results

    def _rule_based_detection(self, logs: List[dict]) -> List[dict]:
        """Simple rule-based detection when model isn't trained"""
        results = []
        
        for log in logs:
            memory_pct = (log.get("used_memory", 0) / log.get("total_memory", 1)) * 100
            process_count = len(log.get("processes", []))
            cpu_usage = log.get("cpu_usage", 0)
            
            # Basic anomaly rules
            is_anomaly = (
                memory_pct > 90 or
                process_count > 400 or
                process_count < 10 or
                cpu_usage > 95
            )
            
            score = -0.5 if is_anomaly else 0.1
            
            results.append({
                "log": log,
                "is_anomaly": is_anomaly,
                "score": score
            })
            
            if is_anomaly:
                print(f"⚠️  Rule-based anomaly: Memory: {memory_pct:.1f}%, Processes: {process_count}")
        
        return results

    def get_feature_info(self):
        return {
            "feature_names": self.feature_names,
            "trained": self.trained
        }