from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.rag import stream_ask, clear_session
from routers.ingest import video_store
import json
import asyncio

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    question: str


@router.post("/chat")
async def chat(request: ChatRequest):
    if not video_store:
        raise HTTPException(
            status_code=400,
            detail="No videos ingested yet. Call /ingest first."
        )

    async def generate():
        full_answer = ""
        citations = []

        loop = asyncio.get_event_loop()
        from concurrent.futures import ThreadPoolExecutor

        chunks = []
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                lambda: list(stream_ask(
                    session_id=request.session_id,
                    question=request.question,
                    video_metadata=video_store,
                ))
            )

        for chunk in result:
            if isinstance(chunk, dict) and chunk.get("type") == "citations":
                citations = chunk["citations"]
            else:
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'content': full_answer, 'citations': citations})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@router.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    clear_session(session_id)
    return {"message": f"Session {session_id} cleared."}