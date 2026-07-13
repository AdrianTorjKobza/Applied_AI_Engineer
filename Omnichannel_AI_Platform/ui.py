import streamlit as st
import requests
import time

st.set_page_config(page_title="AI Campaign Builder", page_icon="🚀", layout="centered")

st.title("Omnichannel AI Campaign Builder")
st.markdown("Generate SEO text and images seamlessly using our background worker architecture.")

# 1. Pre-populated inputs for testing
default_specs = "A highly durable, water-resistant smartwatch with a 7-day battery life, heart-rate monitor, and GPS."
default_audience = "Fitness enthusiasts and outdoor adventurers aged 20-40."

st.subheader("Campaign Requirements")
specs = st.text_area("Product Specifications", value=default_specs, height=100)
audience = st.text_input("Target Audience", value=default_audience)

if st.button("Generate AI Assets", type="primary"):
    
    # 2. Hit the REST API to queue the job
    rest_url = "http://web:8000/api/v1/launch"
    payload = {"product_specs": specs, "target_audience": audience}
    
    with st.spinner("Pushing job to queue..."):
        try:
            response = requests.post(rest_url, json=payload)
            response.raise_for_status()
            job_id = response.json()["job_id"]
            st.success(f"Job Queued Successfully! (ID: {job_id})")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
            st.stop()

    st.divider()
    st.subheader("AI Processing Status")
    status_placeholder = st.empty()
    
    # 3. Poll the GraphQL API for the results
    graphql_url = "http://web:8000/graphql"
    query = """
    query GetMyCampaign($id: String!) {
      job(id: $id) {
        status
        assets {
          assetType
          content
          metadata {
            seoTags
            altText
          }
        }
      }
    }
    """
    
    # Simple polling loop
    while True:
        try:
            gql_response = requests.post(
                graphql_url, 
                json={"query": query, "variables": {"id": job_id}}
            )
            data = gql_response.json().get("data", {}).get("job", {})
            status = data.get("status", "UNKNOWN")
            
            if status == "COMPLETED":
                status_placeholder.success("✅ AI Generation Complete!")
                
                # Render the resulting assets
                assets = data.get("assets", [])
                for asset in assets:
                    with st.expander(f"View {asset['assetType']} Asset", expanded=True):
                        if asset['assetType'] == "IMAGE":
                            st.code(f"File saved to: {asset['content']}")
                        else:
                            st.write(asset['content'])
                            
                        if asset['metadata']:
                            st.json(asset['metadata'])
                break
                
            elif status == "FAILED":
                status_placeholder.error("❌ Job Failed in the background worker.")
                break
                
            else:
                status_placeholder.info(f"⏳ Current Status: **{status}** ... (Waiting for local Ollama to finish)")
                time.sleep(3) # Wait 3 seconds before querying GraphQL again
                
        except Exception as e:
            status_placeholder.error("GraphQL connection lost.")
            break