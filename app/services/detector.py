# app/services/detector.py
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self):
        # Initialize Isolation Forest with sensible defaults
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self.trained = False

    def fit(self, X):
        self.model.fit(X)
        self.trained = True

    def predict(self, X):
        if not self.trained:
            # Auto-fit with dummy baseline so predict doesn’t break
            self.fit([[0] * len(X[0])])
        preds = self.model.predict(X)
        scores = self.model.decision_function(X)
        return preds, scores

    def is_trained(self):
        return self.trained
