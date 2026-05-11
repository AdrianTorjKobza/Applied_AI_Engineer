from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)


def evaluate_model(y_true, y_pred):
    report = classification_report(y_true, y_pred)
    matrix = confusion_matrix(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, y_pred)

    return {
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "roc_auc": roc_auc,
    }