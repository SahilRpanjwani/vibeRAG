from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ingest, chat

app = FastAPI(
    title="vibeRAG API",
    description="RAG chatbot for social media video analysis",
    version="1.0.0"
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "vibeRAG API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}