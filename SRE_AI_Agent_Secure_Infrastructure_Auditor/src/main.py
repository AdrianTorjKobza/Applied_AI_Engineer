# src/main.py
import os
import jwt
from jwt import PyJWKClient
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from langchain_core.messages import HumanMessage

from config import settings
from schemas import PromptRequest
from agent import app_graph

app = FastAPI(title="Secure SRE Agent API")
security = HTTPBearer()

# Let PyJWT dynamically manage caching and fetching the correct Keycloak keys
jwks_client = PyJWKClient(settings.jwks_url)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validates the JWT and enforces Role-Based Access Control (RBAC)."""
    token = credentials.credentials
    
    try:
        # 1. Dynamically find the correct public key using the token's Header (kid)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # 2. Decode and verify the token using that specific key
        decoded_token = jwt.decode(
            token, 
            signing_key.key, 
            algorithms=["RS256"], 
            options={"verify_aud": False} 
        )
        
        # 3. Enforce Least Privilege via Keycloak Role
        realm_access = decoded_token.get("realm_access", {})
        if "SRE_Admin" not in realm_access.get("roles", []):
            raise HTTPException(status_code=403, detail="Access Denied: Missing SRE_Admin role")
            
        return decoded_token
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWKClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch matching public key: {str(e)}")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@app.post("/api/v1/agent/audit")
async def run_audit_agent(request: PromptRequest, user_token: dict = Depends(verify_token)):
    """
    Secure endpoint to trigger the LangGraph SRE Audit.
    Requires a valid Keycloak Bearer token.
    """
    dummy_key = os.getenv("DUMMY_API_KEY", "NOT_INJECTED_YET")
    
    initial_state = {
        "messages": [HumanMessage(content=request.prompt)],
        "dummy_api_key": dummy_key
    }
    
    result = app_graph.invoke(initial_state)
    
    return {
        "authenticated_user": user_token.get("preferred_username", "Unknown"),
        "vault_secret_status": "Successfully Loaded" if dummy_key != "NOT_INJECTED_YET" else "Missing",
        "agent_response": result["messages"][-1].content
    }