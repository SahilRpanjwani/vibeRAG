from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.scraper import scrape_video
from utils.chunker import chunk_transcript
from services.embedder import embed_and_store, clear_collection
import asyncio
from concurrent.futures import ThreadPoolExecutor

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


executor = ThreadPoolExecutor()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_videos(request: IngestRequest):
    try:
        def run_ingest():
            video_store.clear()

            video_a = scrape_video(request.url_a, "A")
            video_b = scrape_video(request.url_b, "B")

            chunks_a = chunk_transcript(video_a["transcript"], "A")
            if chunks_a:
                embed_and_store(chunks_a, video_a)

            chunks_b = chunk_transcript(video_b["transcript"], "B")
            if chunks_b:
                embed_and_store(chunks_b, video_b)

            video_store["A"] = {k: v for k, v in video_a.items() if k != "transcript"}
            video_store["B"] = {k: v for k, v in video_b.items() if k != "transcript"}

            return video_store

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, run_ingest)

        return IngestResponse(
            message="Both videos ingested successfully.",
            video_a=video_store["A"],
            video_b=video_store["B"],
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
