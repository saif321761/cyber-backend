# app/core/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "development"
    API_KEY: str
    N8N_WEBHOOK_URL: str | None = None
    MODEL_DIR: Path = Path("./models")
    MODEL_PATH: Path = Path("./models/model.joblib")
    SCALER_PATH: Path = Path("./models/scaler.joblib")
    MIN_TRAIN_SAMPLES: int = 100
    ISOLATIONFOREST_N_ESTIMATORS: int = 100
    ISOLATIONFOREST_CONTAMINATION: float | str = "auto"

    # pydantic-settings v2+ config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

# instantiate settings and ensure model directory exists
settings = Settings()
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
