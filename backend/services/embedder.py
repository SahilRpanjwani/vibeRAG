from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "video_transcripts"

# Load embedding model once at startup
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ChromaDB client
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_or_create_collection():
    return chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def embed_and_store(chunks: list[dict], video_metadata: dict):
    """
    Takes chunks from chunker + full video metadata dict.
    Embeds each chunk and stores in ChromaDB.
    """
    collection = get_or_create_collection()

    texts = [c["text"] for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()

    ids = [f"{video_metadata['label']}_{c['chunk_index']}" for c in chunks]

    metadatas = [
        {
            "video_id": video_metadata["label"],
            "platform": video_metadata["platform"],
            "title": video_metadata["title"],
            "creator": video_metadata["creator"],
            "views": video_metadata["views"],
            "likes": video_metadata["likes"],
            "comments": video_metadata["comments"],
            "engagement_rate": video_metadata["engagement_rate"],
            "follower_count": video_metadata["follower_count"],
            "upload_date": video_metadata.get("upload_date", ""),
            "duration": video_metadata.get("duration", 0),
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Stored {len(chunks)} chunks for Video {video_metadata['label']}")


def query_collection(query: str, video_ids: list[str] = None, n_results: int = 4) -> list[dict]:
    """
    Query ChromaDB for relevant chunks.
    Optionally filter by video_id (e.g. ['A', 'B']).
    """
    collection = get_or_create_collection()

    query_embedding = embedding_model.encode([query]).tolist()

    where_filter = {"video_id": {"$in": video_ids}} if video_ids else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return chunks


def clear_collection():
    """Clear all stored chunks — useful for re-ingesting."""
    chroma_client.delete_collection(COLLECTION_NAME)
    print("Collection cleared.")