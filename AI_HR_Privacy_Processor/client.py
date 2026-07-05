import os
import time
import httpx
from dotenv import load_dotenv

# Load variables from the .env file located in the same directory
load_dotenv()

# Read configurations securely from the environment
API_URL = os.getenv("CLIENT_API_URL", "http://localhost:8000/api/v1/hr-documents/analyze")
API_KEY = os.getenv("MOCK_API_KEY")
INPUT_DIR = os.getenv("CLIENT_INPUT_DIR", "input_docs")

def process_batch():
    """Reads all .txt files from the input directory and sends them to the API."""
    
    # Safety check: ensure we actually loaded an API key
    if not API_KEY:
        print("[!] ERROR: MOCK_API_KEY not found. Please ensure your .env file is set up correctly.")
        return

    os.makedirs(INPUT_DIR, exist_ok=True)
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.txt')]
    
    if not files:
        print(f"[!] No .txt files found in '{INPUT_DIR}/'.")
        return

    print(f"[*] Found {len(files)} document(s) in '{INPUT_DIR}/'. Starting batch processing...\n")
    
    headers = {"X-API-Key": API_KEY}
    
    with httpx.Client(timeout=180.0) as client:
        for index, filename in enumerate(files, 1):
            filepath = os.path.join(INPUT_DIR, filename)
            
            print(f"[{index}/{len(files)}] Reading '{filename}'...")
            with open(filepath, 'r', encoding='utf-8') as file:
                document_content = file.read()
                
            payload = {
                "department": "Human Resources",
                "document_text": document_content
            }
            
            print("    -> Transmitting to LangChain pipeline for PII redaction...")
            start_time = time.time()
            
            try:
                response = client.post(API_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                elapsed = time.time() - start_time
                telemetry = data.get("telemetry", {})
                
                print(f"    -> [SUCCESS] Processed in {elapsed:.2f} seconds.")
                print(f"    -> [METRICS] {telemetry.get('tokens_generated')} tokens generated.")
                print(f"    -> [SUMMARY] {data.get('analysis')}\n")
                
            except httpx.HTTPError as exc:
                print(f"    -> [ERROR] Failed to process document. Network or API error: {exc}\n")

if __name__ == "__main__":
    process_batch()