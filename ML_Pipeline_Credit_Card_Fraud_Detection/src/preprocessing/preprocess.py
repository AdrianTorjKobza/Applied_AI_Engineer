import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.utils.config import (
    TEST_SIZE,
    RANDOM_STATE,
    SCALER_PATH,
)

def preprocess_data(df):
    X = df.drop("Class", axis=1)
    y = df["Class"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    joblib.dump(scaler, SCALER_PATH)

    return train_test_split(
        X_scaled,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )