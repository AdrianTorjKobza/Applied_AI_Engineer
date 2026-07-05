from fastapi import FastAPI, Depends, HTTPException

from app.schemas import HRDocumentRequest 
from app.security import verify_api_key
from app.telemetry import log_telemetry
from app.llm_service import analyze_document_with_langchain

app = FastAPI(title="HR Privacy LLM Middleware")

@app.post("/api/v1/hr-documents/analyze", dependencies=[Depends(verify_api_key)])
async def analyze_hr_document(payload: HRDocumentRequest):
    """
    Receives an HR document and delegates it to the LangChain service 
    for privacy-focused summarization and PII redaction.
    """
    try:
        # Pass the payload to our isolated LangChain service
        result = await analyze_document_with_langchain(payload.document_text)
        
        # Log telemetry using the returned metrics
        log_telemetry(
            endpoint="/api/v1/hr-documents/analyze", 
            latency=result["latency"], 
            tokens=result["tokens"], 
            status_code=200
        )

        return {
            "status": "success",
            "analysis": result["text"],
            "telemetry": {
                "tokens_generated": result["tokens"],
                "latency_seconds": round(result["latency"], 2)
            }
        }

    except Exception as exc:
        # Catch any LangChain or connection failures
        log_telemetry("/api/v1/hr-documents/analyze", 0.0, 0, 503)
        raise HTTPException(
            status_code=503, 
            detail=f"AI processing pipeline failed: {str(exc)}"
        )