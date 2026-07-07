from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler
from langchain_ollama import ChatOllama
from app.agent import agent_executor
from app.config import settings

app = FastAPI(title="DevOps Responder Agent")

# Langfuse Tracing Handler
langfuse_handler = CallbackHandler()

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default-thread"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.message)]}
        config = {
            "configurable": {"thread_id": request.thread_id},
            "callbacks": [langfuse_handler]
        }
        
        result = agent_executor.invoke(inputs, config=config)
        return {"response": result["messages"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph-mermaid")
async def get_mermaid_graph():
    return {"mermaid_string": agent_executor.get_graph().draw_mermaid()}