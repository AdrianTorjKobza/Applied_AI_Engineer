from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from src.utils.config import DRIFT_THRESHOLD


def detect_drift(reference_df, current_df):
    report = Report(metrics=[DataDriftPreset()])

    report.run(
        reference_data=reference_df,
        current_data=current_df,
    )

    report.save_html("artifacts/reports/drift_report.html")
    result = report.as_dict()
    drift_score = result["metrics"][0]["result"]["dataset_drift"]

    return drift_score


def should_retrain(drift_score, f1_score):
    return drift_score > DRIFT_THRESHOLD or f1_score < 0.80