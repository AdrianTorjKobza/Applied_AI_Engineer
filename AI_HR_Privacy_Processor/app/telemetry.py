import csv
import os
from datetime import datetime
from app.config import TELEMETRY_LOG_DIR

os.makedirs(TELEMETRY_LOG_DIR, exist_ok=True)
CSV_FILE = os.path.join(TELEMETRY_LOG_DIR, "metrics.csv")

def log_telemetry(endpoint: str, latency: float, tokens: int, status_code: int):
    """Appends a new row of telemetry data to the CSV file."""
    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Endpoint", "Latency_Sec", "Tokens_Generated", "HTTP_Status"])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, endpoint, f"{latency:.4f}", tokens, status_code])