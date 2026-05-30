from services.rag import ask

meta = {
    "A": {
        "title": "Never Gonna Give You Up",
        "creator": "Rick Astley",
        "views": 1777614379,
        "likes": 19127196,
        "comments": 2400000,
        "engagement_rate": 1.211,
        "follower_count": 4500000,
        "upload_date": "20091025",
        "duration": 213
    }
}

result = ask("test-session", "What is the engagement rate of video A?", meta)
print(result["answer"])
print("---")
print(f"{len(result['citations'])} citations")