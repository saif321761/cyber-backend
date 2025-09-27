# Cybersecurity Backend

A FastAPI backend for collecting logs from desktop (Tauri) and mobile (React Native) apps, detecting anomalies using Isolation Forest, and sending alerts via n8n workflows (Telegram, Firebase, email).

---

## Features

- `/logs` endpoint: Receives log data from apps
- `/alerts` endpoint: Pushes manual alerts
- Anomaly detection with Isolation Forest
- Integration with n8n for automated alerts
- Dockerized for easy deployment
- Supports async processing of logs

---

## Tech Stack

- Python 3.11+
- FastAPI
- scikit-learn (Isolation Forest)
- Docker & Docker Compose
- n8n workflow integration

---