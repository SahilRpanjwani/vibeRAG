import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from utils.metadata import compute_engagement_rate


def extract_youtube_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path[1:]
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]
    raise ValueError(f"Invalid YouTube URL: {url}")


def scrape_youtube(url: str) -> dict:
    video_id = extract_youtube_id(url)

    # Get transcript
    ytt = YouTubeTranscriptApi()
    fetched = ytt.fetch(video_id)
    transcript = " ".join([t.text for t in fetched])

    # Get metadata via yt-dlp
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    views = info.get("view_count") or 0

    return {
        "platform": "youtube",
        "video_id": video_id,
        "url": url,
        "title": info.get("title"),
        "creator": info.get("uploader"),
        "channel_url": info.get("channel_url"),
        "follower_count": info.get("channel_follower_count") or 0,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "hashtags": info.get("tags") or [],
        "engagement_rate": compute_engagement_rate(likes, comments, views),
        "transcript": transcript,
    }


def scrape_instagram(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "cookiefile": None,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Instagram often doesn't return like/comment counts without auth
    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    views = info.get("view_count") or 0

    # No transcript API for Instagram — we'll handle via Whisper later
    # For now return metadata only, transcript will be empty string
    transcript = info.get("description") or ""

    return {
        "platform": "instagram",
        "video_id": info.get("id"),
        "url": url,
        "title": info.get("title") or info.get("description", "")[:80],
        "creator": info.get("uploader") or info.get("channel"),
        "channel_url": info.get("channel_url") or "",
        "follower_count": info.get("channel_follower_count") or 0,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "hashtags": info.get("tags") or [],
        "engagement_rate": compute_engagement_rate(likes, comments, views),
        "transcript": transcript,
    }


def scrape_video(url: str, video_label: str) -> dict:
    """
    Main entry point. Detects platform and scrapes accordingly.
    video_label: 'A' or 'B'
    """
    if "youtube.com" in url or "youtu.be" in url:
        data = scrape_youtube(url)
    elif "instagram.com" in url:
        data = scrape_instagram(url)
    else:
        raise ValueError(f"Unsupported platform for URL: {url}")

    data["label"] = video_label
    return data