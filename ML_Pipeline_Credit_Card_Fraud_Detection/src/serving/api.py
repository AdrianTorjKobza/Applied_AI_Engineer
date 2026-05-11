from fastapi import FastAPI
from pydantic import BaseModel

import torch
import joblib
import numpy as np

from src.training.train import FraudNet
from src.utils.config import MODEL_PATH, SCALER_PATH


app = FastAPI(title="Fraud Detection API")


class PredictionInput(BaseModel):
    features: list


model = FraudNet(30)
model.load_state_dict(torch.load(MODEL_PATH))
model.eval()

scaler = joblib.load(SCALER_PATH)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(data: PredictionInput):
    features = np.array(data.features).reshape(1, -1)

    scaled = scaler.transform(features)

    tensor = torch.FloatTensor(scaled)

    with torch.no_grad():
        prediction = model(tensor).item()

    return {
        "fraud_probability": prediction,
        "is_fraud": prediction > 0.5,
    }