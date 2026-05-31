import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "video_transcripts"

# Embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
)

# In-memory chat history per session
_chat_histories: dict[str, list] = {}


def get_history(session_id: str) -> list:
    if session_id not in _chat_histories:
        _chat_histories[session_id] = []
    return _chat_histories[session_id]


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


SYSTEM_PROMPT = """You are a social media analytics assistant helping creators understand their video performance.
You have access to transcripts and metadata for two videos labeled A and B.
Always cite which video (A or B) and which part of the transcript you're referencing.
Be specific, data-driven, and actionable in your responses.

IMPORTANT RULES:
- Engagement rate is already computed as (likes + comments) / views * 100. Never recalculate it.
- Always use the engagement_rate value from metadata directly.
- If views are 0, state engagement rate cannot be computed due to restricted view data.
- Never calculate engagement rate using followers — only views.
- When asked about hooks or the first few seconds, always reference chunk 0 of each video as that contains the opening content.
- Chunk 0 is the beginning of the video transcript. Use it directly when asked about hooks or openings.

Retrieved context from video transcripts:
{context}

Video metadata:
{metadata}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])


def format_docs(docs) -> str:
    formatted = []
    # Sort so chunk 0 always appears first
    sorted_docs = sorted(docs, key=lambda d: (d.metadata.get("video_id", ""), d.metadata.get("chunk_index", 99)))
    for doc in sorted_docs:
        video_id = doc.metadata.get("video_id", "?")
        chunk_idx = doc.metadata.get("chunk_index", "?")
        label = "OPENING/HOOK" if chunk_idx == 0 else f"Chunk {chunk_idx}"
        formatted.append(f"[Video {video_id} - {label}]: {doc.page_content}")
    return "\n\n".join(formatted)


def ask(session_id: str, question: str, video_metadata: dict) -> dict:
    """
    Ask a question about the ingested videos.
    video_metadata: {"A": {...}, "B": {...}}
    """
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Format metadata as string
    meta_str = ""
    for label, meta in video_metadata.items():
        meta_str += (
            f"\nVideo {label}: title='{meta['title']}', "
            f"creator='{meta['creator']}', views={meta['views']}, "
            f"likes={meta['likes']}, comments={meta['comments']}, "
            f"engagement_rate={meta['engagement_rate']}%, "
            f"followers={meta['follower_count']}, "
            f"upload_date={meta.get('upload_date', 'N/A')}, "
            f"duration={meta.get('duration', 'N/A')}s"
        )

    # Retrieve relevant chunks
    docs = retriever.invoke(question)

    # For hook questions always include chunk 0 from both videos
    hook_keywords = ["hook", "first", "opening", "start", "beginning", "seconds"]
    if any(kw in question.lower() for kw in hook_keywords):
        from langchain.schema import Document
        collection = get_vectorstore()._collection
        existing_ids = [d.metadata.get("chunk_index") == 0 and d.metadata.get("video_id") for d in docs]

        for vid_id in ["A", "B"]:
            # Only add if chunk 0 not already in results
            already_included = any(
                d.metadata.get("video_id") == vid_id and d.metadata.get("chunk_index") == 0
                for d in docs
            )
            if not already_included:
                try:
                    result = collection.get(
                        ids=[f"{vid_id}_0"],
                        include=["documents", "metadatas"]
                    )
                    if result["documents"]:
                        hook_doc = Document(
                            page_content=result["documents"][0],
                            metadata=result["metadatas"][0]
                        )
                        docs.append(hook_doc)
                except:
                    pass

    context = format_docs(docs)
    history = get_history(session_id)

    # Build and invoke chain
    chain = prompt | llm | StrOutputParser()

    answer = chain.invoke({
        "context": context,
        "metadata": meta_str,
        "chat_history": history,
        "question": question,
    })

    # Update memory
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))

    # Build citations
    citations = [
        {
            "video_id": doc.metadata.get("video_id"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "text_preview": doc.page_content[:120],
        }
        for doc in docs
    ]

    return {
        "answer": answer,
        "citations": citations,
    }


def clear_session(session_id: str):
    if session_id in _chat_histories:
        del _chat_histories[session_id]


def stream_ask(session_id: str, question: str, video_metadata: dict):
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    meta_str = ""
    for label, meta in video_metadata.items():
        meta_str += (
            f"\nVideo {label}: title='{meta['title']}', "
            f"creator='{meta['creator']}', views={meta['views']}, "
            f"likes={meta['likes']}, comments={meta['comments']}, "
            f"engagement_rate={meta['engagement_rate']}%, "
            f"followers={meta['follower_count']}, "
            f"upload_date={meta.get('upload_date', 'N/A')}, "
            f"duration={meta.get('duration', 'N/A')}s"
        )

    # Retrieve relevant chunks
    docs = retriever.invoke(question)

    # -------------------------------------------------
    # Force-include chunk 0 for hook/first‑seconds questions
    hook_keywords = ["hook", "first", "opening", "start", "beginning", "seconds"]
    if any(kw in question.lower() for kw in hook_keywords):
        from langchain_core.documents import Document  # ensure correct import
        collection = vectorstore._collection

        for vid_id in ["A", "B"]:
            # skip if chunk 0 is already retrieved
            already_included = any(
                d.metadata.get("video_id") == vid_id and d.metadata.get("chunk_index") == 0
                for d in docs
            )
            if not already_included:
                try:
                    result = collection.get(
                        ids=[f"{vid_id}_0"],
                        include=["documents", "metadatas"]
                    )
                    if result["documents"]:
                        docs.append(Document(
                            page_content=result["documents"][0],
                            metadata=result["metadatas"][0]
                        ))
                except Exception:
                    pass
    # -------------------------------------------------

    context = format_docs(docs)
    history = get_history(session_id)

    chain = prompt | llm | StrOutputParser()

    full_answer = ""
    for chunk in chain.stream({
        "context": context,
        "metadata": meta_str,
        "chat_history": history,
        "question": question,
    }):
        full_answer += chunk
        yield chunk

    # Save to memory
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=full_answer))

    # Yield citations as final item
    citations = [
        {
            "video_id": doc.metadata.get("video_id"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "text_preview": doc.page_content[:120],
        }
        for doc in docs
    ]
    yield {"type": "citations", "citations": citations}