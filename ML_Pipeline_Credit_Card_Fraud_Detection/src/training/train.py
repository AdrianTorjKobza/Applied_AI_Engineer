import torch
import torch.nn as nn
import torch.optim as optim
import mlflow

from sklearn.metrics import f1_score

from src.utils.config import (
    EPOCHS,
    LEARNING_RATE,
    MODEL_PATH,
)


class FraudNet(nn.Module):
    def __init__(self, input_dim):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.network(x)


def train_model(X_train, X_test, y_train, y_test):
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.FloatTensor(y_train.values).view(-1, 1)

    X_test_tensor = torch.FloatTensor(X_test)

    model = FraudNet(X_train.shape[1])

    fraud_weight = (len(y_train) - y_train.sum()) / y_train.sum()

    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([fraud_weight], dtype=torch.float32)
    )

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    mlflow.set_experiment("fraud-detection")

    with mlflow.start_run():
        mlflow.log_param("epochs", EPOCHS)
        mlflow.log_param("learning_rate", LEARNING_RATE)

        for epoch in range(EPOCHS):
            optimizer.zero_grad()

            outputs = model(X_train_tensor)
            loss = criterion(outputs, y_train_tensor)

            loss.backward()
            optimizer.step()

        with torch.no_grad():
            predictions = torch.sigmoid(model(X_test_tensor))
            predictions = (predictions.numpy() > 0.5).astype(int)

        f1 = f1_score(y_test, predictions)

        mlflow.log_metric("f1_score", f1)

        torch.save(model.state_dict(), MODEL_PATH)

        mlflow.pytorch.log_model(model, "model")

    return model, f1