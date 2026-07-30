import os
import pickle
import datetime
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Define the FastAPI app
app = FastAPI(
    title="SteerSafe AI API Backend",
    description="Backend API for predicting driving risk from simulated sensor data.",
    version="1.0.0"
)

# Enable CORS so web apps running locally can access the backend endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths for files
MODEL_PATH = os.path.join("backend", "steersafe_model.pkl")
FEATURES_PATH = os.path.join("backend", "feature_columns.pkl")
ALERTS_LOG_PATH = os.path.join("backend", "alerts.log")

# Global variables to store the model and features
model = None
feature_columns = None

@app.on_event("startup")
def load_ml_model():
    global model, feature_columns
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            with open(FEATURES_PATH, "rb") as f:
                feature_columns = pickle.load(f)
            print("Successfully loaded SteerSafe AI model and features!")
        except Exception as e:
            print(f"Error loading model files: {e}")
    else:
        print("Warning: Model files not found. Run scripts/train_model.py first.")

# Pydantic schemas for request validation
class SensorSample(BaseModel):
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float

class PredictionRequest(BaseModel):
    samples: List[SensorSample] # Expecting a 3-second window (approx 30 samples)

class LogRequest(BaseModel):
    message: str
    risk_level: str

# Helper to compute features from window samples
def calculate_window_features(samples: List[SensorSample]) -> dict:
    if len(samples) == 0:
        return {}
        
    ax_vals = [s.ax for s in samples]
    ay_vals = [s.ay for s in samples]
    az_vals = [s.az for s in samples]
    gx_vals = [s.gx for s in samples]
    gy_vals = [s.gy for s in samples]
    gz_vals = [s.gz for s in samples]
    
    feats = {}
    for name, vals in [("ax", ax_vals), ("ay", ay_vals), ("az", az_vals), 
                       ("gx", gx_vals), ("gy", gy_vals), ("gz", gz_vals)]:
        feats[f"{name}_mean"] = np.mean(vals)
        feats[f"{name}_std"] = np.std(vals) if len(vals) > 1 else 0.0
        feats[f"{name}_min"] = np.min(vals)
        feats[f"{name}_max"] = np.max(vals)
        
    return feats

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Welcome to SteerSafe AI Backend API",
        "model_loaded": model is not None
    }

@app.post("/predict")
def predict(request: PredictionRequest):
    global model, feature_columns
    if model is None:
        raise HTTPException(status_code=503, detail="Machine learning model is not loaded. Train the model first.")
        
    if len(request.samples) < 5:
        raise HTTPException(status_code=400, detail="Too few samples. Please provide a full window of sensor data.")
        
    # Extract features
    features_dict = calculate_window_features(request.samples)
    
    # Format into feature array matching training order
    try:
        feature_vector = [features_dict[col] for col in feature_columns]
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Failed to match features: {e}")
        
    # Predict
    prediction = model.predict([feature_vector])[0]
    probabilities = model.predict_proba([feature_vector])[0]
    classes = model.classes_
    prob_dict = {classes[i]: float(probabilities[i]) for i in range(len(classes))}
    
    # Automatically log alerts if prediction is High Risk
    if prediction == "High Risk":
        log_message = f"High acceleration or sudden swerving detected! Real-time alerts broadcasted."
        write_alert_to_file("High Risk", log_message)
        
    return {
        "risk_level": prediction,
        "probabilities": prob_dict,
        "features": features_dict
    }

@app.get("/simulate")
def simulate(behavior: str = "Safe"):
    """
    Simulates a 3-second window of data in real-time based on selected behavior,
    predicts the risk, and logs it. Handy for simple frontends.
    """
    if behavior not in ["Safe", "Moderate Risk", "High Risk"]:
        raise HTTPException(status_code=400, detail="Invalid behavior. Choose Safe, Moderate Risk, or High Risk.")
        
    # Create synthetic window (30 samples)
    n_samples = 30
    ax = np.zeros(n_samples)
    ay = np.zeros(n_samples)
    az = np.ones(n_samples) * 9.81
    gx = np.zeros(n_samples)
    gy = np.zeros(n_samples)
    gz = np.zeros(n_samples)
    
    if behavior == "Safe":
        ax += np.random.normal(0, 0.4, n_samples)
        ay += np.random.normal(0, 0.4, n_samples)
        az += np.random.normal(0, 0.4, n_samples)
        gx += np.random.normal(0, 1.5, n_samples)
        gy += np.random.normal(0, 1.5, n_samples)
        gz += np.random.normal(0, 1.5, n_samples)
    elif behavior == "Moderate Risk":
        ax += np.random.normal(0, 1.0, n_samples)
        ay += np.random.normal(0, 1.0, n_samples)
        az += np.random.normal(0, 1.0, n_samples)
        gx += np.random.normal(0, 7.0, n_samples)
        gy += np.random.normal(0, 7.0, n_samples)
        gz += np.random.normal(0, 7.0, n_samples)
        # Moderate braking event
        ax[10:20] -= 2.0
    else: # High Risk
        ax += np.random.normal(0, 2.2, n_samples)
        ay += np.random.normal(0, 2.2, n_samples)
        az += np.random.normal(0, 2.2, n_samples)
        gx += np.random.normal(0, 15.0, n_samples)
        gy += np.random.normal(0, 15.0, n_samples)
        gz += np.random.normal(0, 15.0, n_samples)
        # Extreme event
        ax[8:18] -= 7.5 # Extreme hard brake
        gz[8:18] += 40.0 # Extreme sharp turn
        
    samples = []
    for i in range(n_samples):
        samples.append(SensorSample(
            ax=float(ax[i]), ay=float(ay[i]), az=float(az[i]),
            gx=float(gx[i]), gy=float(gy[i]), gz=float(gz[i])
        ))
        
    # Execute prediction using current model
    if model is None:
        # Fallback if model training not executed yet
        predicted_risk = behavior
    else:
        features_dict = calculate_window_features(samples)
        feature_vector = [features_dict[col] for col in feature_columns]
        predicted_risk = model.predict([feature_vector])[0]
        
    if predicted_risk == "High Risk":
        write_alert_to_file("High Risk", f"Simulated live high risk alert! Triggered by {behavior} profile.")
    elif predicted_risk == "Moderate Risk":
        write_alert_to_file("Moderate Risk", f"Simulated live moderate risk. Triggered by {behavior} profile.")
        
    # Return both the samples and the predicted risk
    return {
        "behavior_profile": behavior,
        "predicted_risk": predicted_risk,
        "samples": [s.dict() for s in samples]
    }

@app.post("/log_alert")
def log_alert(request: LogRequest):
    write_alert_to_file(request.risk_level, request.message)
    return {"status": "success", "message": "Alert logged."}

@app.get("/logs")
def get_logs(limit: int = 15):
    if not os.path.exists(ALERTS_LOG_PATH):
        return []
        
    logs = []
    try:
        with open(ALERTS_LOG_PATH, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                parts = line.strip().split(" | ", 2)
                if len(parts) == 3:
                    logs.append({
                        "timestamp": parts[0],
                        "risk_level": parts[1],
                        "message": parts[2]
                    })
    except Exception as e:
        print(f"Error reading logs: {e}")
        
    # Return in reverse chronological order (newest first)
    return logs[::-1]

def write_alert_to_file(risk_level: str, message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {risk_level} | {message}\n"
    try:
        with open(ALERTS_LOG_PATH, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write to alert log: {e}")
