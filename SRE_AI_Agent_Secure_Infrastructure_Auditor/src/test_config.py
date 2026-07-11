# src/test_config.py
from config import settings

print(f"Keycloak URL: {settings.keycloak_url}")
print(f"Client ID: {settings.client_id}")
secret = settings.client_secret.get_secret_value()
print(f"Secret Length: {len(secret)}")
print(f"First 4 chars: {secret[:4]}")