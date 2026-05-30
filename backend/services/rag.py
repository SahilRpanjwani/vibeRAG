import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
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
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
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
    for doc in docs:
        video_id = doc.metadata.get("video_id", "?")
        chunk_idx = doc.metadata.get("chunk_index", "?")
        formatted.append(f"[Video {video_id}, Chunk {chunk_idx}]: {doc.page_content}")
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
    """
    Streaming version — yields answer chunks.
    """
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

    docs = retriever.invoke(question)
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

    # Save to memory after streaming completes
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=full_answer))