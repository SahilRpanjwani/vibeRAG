from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.rag import stream_ask, clear_session
from routers.ingest import video_store
import json

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
        citations_sent = False
        full_answer = ""

        for chunk in stream_ask(
            session_id=request.session_id,
            question=request.question,
            video_metadata=video_store,
        ):
            full_answer += chunk
            # Stream answer chunks as SSE
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

        # Send citations at the end
        yield f"data: {json.dumps({'type': 'done', 'content': full_answer})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    clear_session(session_id)
    return {"message": f"Session {session_id} cleared."}