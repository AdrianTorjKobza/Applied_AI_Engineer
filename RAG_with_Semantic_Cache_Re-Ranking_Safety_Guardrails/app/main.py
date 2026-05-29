from app.guardrails import LocalGuardrail
from app.pipeline import LocalRAGPipeline
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

def handle_user_request(query: str) -> dict:
    # Instantiate components
    guardrail = LocalGuardrail()
    pipeline = LocalRAGPipeline()
    
    # Run absolute validation guardrail first
    is_safe, message_or_query = guardrail.validate_query(query)

    if not is_safe:
        return {
            "answer": message_or_query,
            "source": "guardrail_refusal",
            "execution_time_ms": 0
        }
        
    # Execute RAG flow
    return pipeline.run(message_or_query)

if __name__ == "__main__":
    # Seed mock data for verification test run
    from langchain_core.documents import Document
    p = LocalRAGPipeline()
    p.vector_store.add_documents([
        Document(page_content="Our remote work policy requires employees to be present online during core hours: 10 AM to 4 PM."),
        Document(page_content="For hardware distribution, developers receive standard corporate laptops running Windows environments.")
    ])
    
    # Test a typical interaction loop
    print(handle_user_request("What is our remote work policy?"))