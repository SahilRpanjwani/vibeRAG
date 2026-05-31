# vibeRAG

vibeRAG is A full-stack RAG chatbot that lets you drop two social media video URLs and have an AI conversation about their performance — engagement rates, transcript hooks, creator stats, and improvement suggestions.

Built for a technical screening round in ~2 days.

## What it does

- Takes a YouTube URL and an Instagram Reel URL as input
- Scrapes transcript + metadata (views, likes, comments, followers, engagement rate, duration, hashtags)
- Chunks and embeds transcripts into ChromaDB using MiniLM-L6-v2
- Streams RAG responses via LangChain + Groq (LLaMA 3.1) with conversation memory
- Side-by-side video cards + chat panel with suggestion chips

## Tech stack and why

| Layer | Choice | Reason |
|---|---|---|
| Backend | FastAPI | Async-native, perfect for SSE streaming |
| Orchestration | LangChain (LCEL) | Clean chain composition, easy retriever swap |
| Embeddings | all-MiniLM-L6-v2 | Free, runs locally, 384-dim is plenty for transcript chunks |
| Vector DB | ChromaDB | Zero infra, local persistence, swappable to Qdrant/Pinecone at scale |
| LLM | Groq / LLaMA 3.1 8B | Fastest inference available, generous free tier, streaming supported |
| Transcript | youtube-transcript-api + yt-dlp | No headless browser needed, works on Reels too |
| Frontend | React + Vite | Fast dev server, minimal setup |

## Why this stack scales

At 1000 creators/day:
- **ChromaDB → Qdrant** (horizontal scaling, better filtering at volume)
- **Add a job queue** (Celery + Redis) so ingest is async and doesn't block the API
- **Groq free tier → Groq paid or self-hosted Llama** for rate limit headroom
- **MiniLM stays** — it's fast enough and cheap to run on CPU

The bottleneck at scale is Instagram scraping (rate limits, auth walls) — solution is a cookie-authenticated yt-dlp session or a paid scraping API like Apify.

## Chunk size reasoning

300 tokens with 50 overlap. Transcripts are conversational — short chunks give better retrieval precision. Larger chunks (500+) start pulling in irrelevant context and hurt answer quality.

## Known limitations

- Instagram metadata (views, followers, comments) often returns 0 without authentication — Instagram locks this behind login. Likes sometimes come through.
- Instagram Reels don't have a dedicated transcript API — transcript falls back to video description. For production, pipe audio through Whisper.
- YouTube Shorts work fine.

## Setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Add your keys
cp .env.example .env
# Fill in GROQ_API_KEY in .env

uvicorn main:app --reload
```

```bash
# Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## Usage

1. Paste a YouTube URL in Video A
2. Paste an Instagram Reel URL in Video B
3. Hit Analyze Videos — wait ~15-20s for scraping + embedding
4. Ask anything in the chat

## Hosting

Frontend: https://viberag-frontend.onrender.com
Backend: https://mrw4lk3r-viberag-backend.hf.space

Note: YouTube transcript and metadata scraping is blocked by YouTube when running from cloud provider IPs (AWS, GCP, etc.) — this is a known platform restriction affecting all free hosting tiers. The app works fully when run locally as shown in the Loom. Production fix would be residential proxies or the official YouTube Data API v3.

Instagram metadata (views, follower count) is restricted without official Graph API access. Likes and comments come through via yt-dlp. Production fix: Instagram Graph API or Apify.


## NOTE
I built vibeRAG in 2 days — one day for coding and running the whole program, the second for extra checks and hosting. At first everything worked, but then I hit a known Gemini issue: they've started rate limiting much harder than before, and the app stopped working. I found Groq as an alternative — higher limits, great quality, a perfect replacement. After grabbing an API key from GroqCloud, everything sailed smoothly. I kept committing after solving each issue and making updates.

I started with zero knowledge of LangChain, so I used NotebookLM to compile a ton of sources — a whole playlist of hours‑long YouTube videos and multiple websites — and learned from them much more easily and faster. I also used Claude and DeepSeek side‑by‑side. If I got stuck in Claude or needed a deeper explanation, I'd copy the code or error over to DeepSeek. That way I preserved my rate limit in Claude and still understood the code just as well. Sometimes errors are long, so instead of using Claude to explain them, I'd go to DeepSeek to break down the error and trace it myself. Then I'd ask Claude for the best ways to solve it. Occasionally I'd even go to YouTube to see how professionals work through something or pinpoint a specific issue.

Copy‑pasting from AI is easy, but it won't find your bug. You have to know what you did and where it broke — only you can really trace it. That's one thing I'm proud of: I can do that.

The most painstaking work was trying to get Instagram to give more details and information about the Reels. Every free option gave very little data; all the fuller solutions were paid, as I mentioned in my Loom video.

Hosting was simpler but time‑consuming. Leftover commits, uncommitted docs, etc. Even after sorting those, it couldn't fully go through because YouTube doesn't allow transcript and metadata scraping from free‑tier hosted sites, and I don't have the budget for a paid host. I even tried Hugging Face Spaces for the backend (since Render only gives ~512 MB storage and I needed more — Hugging Face gives about 16 GB). I created an account, hosted the backend there, and put the frontend on Render. I thought it was perfect, until I got hit with YouTube's restrictions. At least it all still works perfectly locally.

