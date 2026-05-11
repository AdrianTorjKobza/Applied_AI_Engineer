from src.ingestion.ingest import load_data
from src.preprocessing.preprocess import preprocess_data
from src.training.train import train_model
from src.drift.detect_drift import detect_drift
from src.drift.detect_drift import should_retrain

import sys

if sys.version_info >= (3, 12):
    raise RuntimeError(
        "This project currently supports Python 3.11.x only."
    )


def run_pipeline():
    print("Loading data...")
    df = load_data()

    print("Preprocessing data...")
    X_train, X_test, y_train, y_test = preprocess_data(df)

    print("Training model...")

    model, f1 = train_model(
        X_train,
        X_test,
        y_train,
        y_test,
    )

    print(f"F1 Score: {f1}")

    print("Checking drift...")

    reference_df = df.sample(frac=0.5, random_state=42)
    current_df = df.sample(frac=0.5, random_state=1)

    drift_score = detect_drift(reference_df, current_df)

    print(f"Drift Score: {drift_score}")

    retrain = should_retrain(drift_score, f1)

    if retrain:
        print("Retraining triggered")
    else:
        print("Model stable")


if __name__ == "__main__":
    run_pipeline()