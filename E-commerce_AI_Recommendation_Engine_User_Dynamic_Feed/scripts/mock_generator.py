# CLI script to simulate user traffic

import requests
import time
import random
import json

API_URL = "http://localhost:8000/v1/events"
CATEGORIES = ["running_gear", "weightlifting", "outdoor"]

def generate_traffic():
    print("Starting simulated user traffic...")
    
    for i in range(1, 20):
        # Simulate a user dwelling on a product
        payload = {
            "user_id": f"user_{random.randint(100, 105)}",
            "event_type": "dwell_time",
            "product_id": f"prod_{random.randint(1000, 9999)}",
            "category": random.choice(CATEGORIES),
            "attributes": {
                "duration_seconds": random.randint(10, 120),
                "scrolled_percentage": random.randint(20, 100)
            }
        }
        
        response = requests.post(API_URL, json=payload)
        print(f"Sent: {payload['category']} | Status: {response.status_code}")
        
        # Random sleep to simulate human navigation speed
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    generate_traffic()