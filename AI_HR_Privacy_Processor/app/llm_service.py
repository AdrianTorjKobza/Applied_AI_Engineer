import time
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app import config

# LangChain expects the base URL (e.g., http://localhost:11434), 
# so we strip the /api/generate suffix from our existing config.
base_url = config.OLLAMA_URL.replace("/api/generate", "")

# 1. Initialize the LLM wrapper
# Temperature is set to 0.0 to ensure strict, deterministic redaction and factual summarization
llm = ChatOllama(
    base_url=base_url,
    model=config.TARGET_MODEL,
    temperature=0.0, 
)

# 2. Define the Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a strict legal and HR assistant. Your job is to summarize the following document and extract key action items. You MUST redact any Personally Identifiable Information (PII) such as names or IDs, replacing them with [REDACTED]."),
    ("human", "Document: {document_text}")
])

# 3. Create the LCEL (LangChain Expression Language) Chain
# The | operator pipes the formatted prompt directly into the LLM
hr_processing_chain = prompt_template | llm

async def analyze_document_with_langchain(document_text: str) -> dict:
    """Executes the LangChain pipeline and captures metadata for telemetry."""
    start_time = time.time()
    
    # ainvoke() runs the chain asynchronously
    response = await hr_processing_chain.ainvoke({"document_text": document_text})
    
    latency = time.time() - start_time
    
    # LangChain's ChatOllama wrapper automatically captures Ollama's 
    # native response data in the 'response_metadata' dictionary
    metadata = response.response_metadata
    tokens = metadata.get("eval_count", 0)
    
    return {
        "text": response.content,
        "tokens": tokens,
        "latency": latency
    }