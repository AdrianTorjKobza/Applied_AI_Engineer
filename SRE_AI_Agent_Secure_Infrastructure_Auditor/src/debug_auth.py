# src/debug_auth.py
import requests
from config import settings

url = f"{settings.keycloak_url}/realms/{settings.realm}/protocol/openid-connect/token"
data = {
    "client_id": settings.client_id,
    "client_secret": settings.client_secret.get_secret_value(),
    "grant_type": "client_credentials"
}

print(f"Attempting to connect to: {url}")
response = requests.post(url, data=data)

if response.status_code == 200:
    print("SUCCESS! Keycloak accepted the credentials.")
else:
    print(f"FAILED! Status Code: {response.status_code}")
    print(f"Response: {response.json()}")