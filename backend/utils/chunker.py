from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_transcript(transcript: str, video_label: str) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_text(transcript)

    return [
        {
            "text": chunk,
            "video_id": video_label,
            "chunk_index": i
        }
        for i, chunk in enumerate(chunks)
    ]