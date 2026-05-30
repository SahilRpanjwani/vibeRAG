from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.scraper import scrape_video
from utils.chunker import chunk_transcript
from services.embedder import embed_and_store, clear_collection

router = APIRouter()

# In-memory store for video metadata (used by chat router)
video_store: dict = {}


class IngestRequest(BaseModel):
    url_a: str
    url_b: str


class IngestResponse(BaseModel):
    message: str
    video_a: dict
    video_b: dict


@router.post("/ingest", response_model=IngestResponse)
async def ingest_videos(request: IngestRequest):
    try:
        # Clear previous session data
        clear_collection()
        video_store.clear()

        # Scrape both videos
        video_a = scrape_video(request.url_a, "A")
        video_b = scrape_video(request.url_b, "B")

        # Chunk and embed — skip if transcript is empty
        chunks_a = chunk_transcript(video_a["transcript"], "A")
        if chunks_a:
            embed_and_store(chunks_a, video_a)

        chunks_b = chunk_transcript(video_b["transcript"], "B")
        if chunks_b:
            embed_and_store(chunks_b, video_b)

        # Store metadata for chat router to use
        video_store["A"] = {k: v for k, v in video_a.items() if k != "transcript"}
        video_store["B"] = {k: v for k, v in video_b.items() if k != "transcript"}

        return IngestResponse(
            message="Both videos ingested successfully.",
            video_a=video_store["A"],
            video_b=video_store["B"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))