from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.chatbot import chat, chat_stream
import os
import logging
import traceback
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="i95Dev Chatbot API")

# Log env var status at startup (masked for security)
for key in ["GROQ_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX_NAME", "FRONTEND_URL", "HF_TOKEN"]:
    val = os.getenv(key, "")
    status = f"{val[:4]}..." if len(val) > 4 else "NOT SET"
    logger.info(f"ENV {key}: {status}")

# CORS — supports localhost dev + any Render-deployed frontend URL
_origins = list({
    "http://localhost:3000",
    "http://localhost:8000",
    *[u.strip() for u in os.getenv("FRONTEND_URL", "").split(",") if u.strip()],
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str
    id: Optional[str] = None
    createdAt: Optional[str] = None

    class Config:
        extra = "allow"


class ChatRequest(BaseModel):
    messages: List[Any]


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "i95Dev Chatbot API is running"}


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages list cannot be empty")

        history = []
        for msg in request.messages[:-1]:
            if isinstance(msg, dict):
                history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            else:
                history.append({
                    "role": getattr(msg, "role", "user"),
                    "content": getattr(msg, "content", "")
                })

        last_msg = request.messages[-1]
        user_message = (
            last_msg.get("content")
            if isinstance(last_msg, dict)
            else getattr(last_msg, "content", "")
        )

        response = chat(user_message, history)
        return ChatResponse(content=response)

    except Exception as e:
        logger.error(f"CHAT ERROR: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- STREAMING ENDPOINT ---------------- #

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    True token-level streaming endpoint for assistant-ui
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages list cannot be empty")

        history = []
        for msg in request.messages[:-1]:
            if isinstance(msg, dict):
                history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            else:
                history.append({
                    "role": getattr(msg, "role", "user"),
                    "content": getattr(msg, "content", "")
                })

        last_msg = request.messages[-1]
        user_message = (
            last_msg.get("content")
            if isinstance(last_msg, dict)
            else getattr(last_msg, "content", "")
        )

        def event_stream():
            for token in chat_stream(user_message, history):
                yield token

        return StreamingResponse(
            event_stream(),
            media_type="text/plain"
        )

    except Exception as e:
        logger.error(f"STREAM ERROR: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
