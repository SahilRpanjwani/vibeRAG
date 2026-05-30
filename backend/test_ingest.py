from services.scraper import scrape_video
from utils.chunker import chunk_transcript
from services.embedder import embed_and_store, clear_collection

clear_collection()

print("Scraping video A...")
video_a = scrape_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "A")
print(f"Got: {video_a['title']}")

print("Scraping video B...")
video_b = scrape_video("https://www.instagram.com/reel/DY6ouGDvhnz/", "B")
print(f"Got: {video_b['title']}")

print("Embedding A...")
chunks_a = chunk_transcript(video_a["transcript"], "A")
if chunks_a:
    embed_and_store(chunks_a, video_a)

print("Embedding B...")
chunks_b = chunk_transcript(video_b["transcript"], "B")
if chunks_b:
    embed_and_store(chunks_b, video_b)

print("Done!")