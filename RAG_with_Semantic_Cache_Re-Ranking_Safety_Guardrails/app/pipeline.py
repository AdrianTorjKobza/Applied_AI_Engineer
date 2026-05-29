import ssl
import os
import requests
import time

# --- ENVIRONMENT & SSL FIXES ---
# 1. Standard library SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context

# 2. Aggressive requests bypass (Fixes the FlashRank download error)
old_request = requests.Session.request
def unverified_request(*args, **kwargs):
    kwargs['verify'] = False
    return old_request(*args, **kwargs)
requests.Session.request = unverified_request

# 3. Suppress the annoying "InsecureRequestWarning"
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 4. Silence ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# --- STABLE IMPORTS (0.3.x / 1.0 COMPATIBLE) ---
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.documents import Document

class LocalRAGPipeline:
    def __init__(self, db_path: str = "./chroma_db"):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        self.vector_store = Chroma(
            persist_directory=db_path, 
            embedding_function=self.embeddings,
            collection_name="kb_docs"
        )
        
        self.cache_store = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings,
            collection_name="semantic_cache"
        )
        
        # Local re-ranker
        self.reranker = FlashrankRerank(top_n=3)
        self.similarity_threshold = 0.85

    def check_semantic_cache(self, query: str) -> str | None:
        try:
            results = self.cache_store.similarity_search_with_relevance_scores(query, k=1)
            if results and results[0][1] >= self.similarity_threshold:
                return results[0][0].metadata.get("cached_response")
        except Exception:
            return None
        return None

    def update_semantic_cache(self, query: str, response: str):
        doc = Document(page_content=query, metadata={"cached_response": response})
        self.cache_store.add_documents([doc])

    def query_local_llm(self, prompt: str) -> str:
        try:
            url = "http://localhost:11434/api/generate"
            payload = {"model": "llama3", "prompt": prompt, "stream": False}
            response = requests.post(url, json=payload, timeout=60)
            return response.json().get("response", "Error reading stream.")
        except Exception as e:
            return f"Local generation failure: {str(e)}"

    def run(self, query: str) -> dict:
        start_time = time.time()
        
        # 1. Cache Check
        cached_answer = self.check_semantic_cache(query)
        if cached_answer:
            return {"answer": cached_answer, "source": "semantic_cache", "execution_time_ms": int((time.time() - start_time) * 1000)}
        
        # 2. Base Retrieval (Fetch top 10 natively)
        retrieved_docs = self.vector_store.similarity_search(query, k=10)
        
        if not retrieved_docs:
            return {"answer": "No relevant context found.", "source": "empty_fallback"}
            
        # 3. Manual Re-ranking (Bypassing broken Langchain Retrievers!)
        # We pass the raw documents directly into the FlashRank compressor
        ranked_docs = self.reranker.compress_documents(documents=retrieved_docs, query=query)
        
        # 4. Generation
        context = "\n\n".join([doc.page_content for doc in ranked_docs])
        system_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        llm_response = self.query_local_llm(system_prompt)
        self.update_semantic_cache(query, llm_response)
        
        return {
            "answer": llm_response, 
            "source": "llm_generation", 
            "execution_time_ms": int((time.time() - start_time) * 1000)
        }