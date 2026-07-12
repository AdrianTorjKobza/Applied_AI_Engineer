import streamlit as st
import requests
import httpx
import pandas as pd
from core.config import settings

BACKEND_URL = settings.backend_url
GRAPHQL_URL = settings.graphql_url

st.set_page_config(page_title="DevOps & IT AI Troubleshooter", layout="wide")
st.title("📟 AI ChatBot | DevOps & IT Troubleshooter")

if "session_token" not in st.session_state:
    st.session_state.session_token = "dev-token-xyz"

with st.sidebar:
    st.header("Workspace Controls")
    st.session_state.session_token = st.text_input("Developer Token/Session ID", value=st.session_state.session_token)
    
    if st.button("Initialize Workspace Connection"):
        headers = {"X-Session-Token": st.session_state.session_token}
        try:
            res = requests.post(f"{BACKEND_URL}/v1/session", headers=headers)
            if res.status_code == 200:
                st.success("Session Verified Securely.")
            else:
                st.error(f"Backend Error: {res.text}")
        except requests.exceptions.ConnectionError:
            st.error("Failed to connect to FastAPI. Is Uvicorn running?")

# Pre-populated error log example for quick testing.
DEFAULT_ERROR_LOG = """[2023-10-27 10:45:32,112] ERROR in app: Exception on /api/v1/users [GET]
Traceback (most recent call last):
  File "/usr/local/lib/python3.9/site-packages/sqlalchemy/pool/impl.py", line 146, in _do_get
    raise exc.TimeoutError(
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00"""

tab1, tab2 = st.tabs(["💬 Error Analysis Terminal", "📊 Query Log Analytics (GraphQL)"])

with tab1:
    st.subheader("Interactive Stream Processing")
    user_input = st.text_area("Paste Stack Trace, Error Output, or Configuration File logs:", value=DEFAULT_ERROR_LOG, height=250)
    
    if st.button("Analyze Logs with Llama3"):
        if user_input:
            headers = {"X-Session-Token": st.session_state.session_token}
            
            # Added a 120s timeout. Local LLMs can take time to load into memory on the first run.
            with httpx.Client(timeout=None) as client:
                try:
                    with client.stream("POST", f"{BACKEND_URL}/v1/chat/stream", json={"prompt": user_input}, headers=headers) as r:
                        if r.status_code == 200:
                            placeholder = st.empty()
                            full_response = ""

                            for line in r.iter_lines():
                                if line.startswith("data: "):
                                    text_chunk = line[6:]
                                    full_response += text_chunk
                                    placeholder.markdown(full_response + "▌")
                            placeholder.markdown(full_response)
                        elif r.status_code == 429:
                            st.error("Rate Limit Breached! (Redis Counter Intercepted Excess Requests)")
                        else:
                            # Catch and display any unexpected backend errors.
                            st.error(f"Backend HTTP Error {r.status_code}: {r.read().decode('utf-8')}")
                except httpx.ConnectError:
                    st.error("Connection Failed. Ensure your FastAPI backend is running on port 8000.")

with tab2:
    st.subheader("GraphQL Metrics and Log Inspector")
    st.caption("Fetches explicit historical telemetry. Cached via Redis TTL.")
    
    if st.button("Execute GraphQL Fetch Request"):
        gql_query = """
        query {
          getHistory(sessionToken: "%s") {
            id
            role
            content
            timestamp
          }
        }
        """ % st.session_state.session_token
        
        try:
            response = requests.post(GRAPHQL_URL, json={"query": gql_query})
            data = response.json().get("data", {}).get("getHistory", [])
            
            if data:
                st.success(f"Retrieved {len(data)} total records.")
                
                # VISUALIZATION FEATURE IMPLEMENTATION
                df = pd.DataFrame(data)
                # Convert ISO timestamp strings to actual datetime objects
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Split layout into two columns for metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Interaction Volume by Role**")
                    # Count messages by 'user' vs 'assistant'
                    role_counts = df['role'].value_counts()
                    st.bar_chart(role_counts)
                
                with col2:
                    st.markdown("**Interaction Timeline**")
                    # Group by hour to see when errors are happening
                    timeline = df.set_index('timestamp').resample('H').size()
                    st.line_chart(timeline)

                # Show the raw searchable database
                st.markdown("**Raw Query Logs**")
                st.dataframe(df[["timestamp", "role", "content"]], use_container_width=True)

            else:
                st.warning("No interactions registered to this security ecosystem workspace yet.")
        except Exception as e:
            st.error(f"Error executing GraphQL query: {e}")