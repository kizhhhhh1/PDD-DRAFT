import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_read_main():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"
        assert "SteerSafe AI Backend API" in response.json()["message"]

def test_simulate_valid_behavior():
    with TestClient(app) as client:
        response = client.get("/simulate?behavior=Safe")
        assert response.status_code == 200
        assert "predicted_risk" in response.json()
        assert "behavior_profile" in response.json()

def test_simulate_invalid_behavior():
    with TestClient(app) as client:
        response = client.get("/simulate?behavior=SuperDangerous")
        assert response.status_code == 400
        assert "Invalid behavior" in response.json()["detail"]

def test_predict_too_few_samples():
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={"samples": [{"ax": 0.0, "ay": 0.0, "az": 9.8, "gx": 0.0, "gy": 0.0, "gz": 0.0}]}
        )
        assert response.status_code == 400
        assert "Too few samples" in response.json()["detail"]
