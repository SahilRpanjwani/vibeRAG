import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from utils.metadata import compute_engagement_rate


def extract_youtube_id(url: str) -> str:
    parsed = urlparse(url)

    # Handle youtu.be short links
    if parsed.hostname in ("youtu.be",):
        return parsed.path[1:]

    # Handle YouTube Shorts
    if "/shorts/" in parsed.path:
        return parsed.path.split("/shorts/")[-1].split("?")[0]

    # Handle regular youtube.com/watch?v=
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        video_id = parse_qs(parsed.query).get("v", [None])[0]
        if video_id:
            return video_id

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
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        likes = info.get("like_count") or 0
        comments = info.get("comment_count") or 0
        views = info.get("view_count") or 0
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

    except Exception as e:
        print(f"Instagram scrape failed: {e}")
        # Return a placeholder so the app doesn't crash
        video_id = url.split("/reel/")[-1].split("/")[0] if "/reel/" in url else "unknown"
        return {
            "platform": "instagram",
            "video_id": video_id,
            "url": url,
            "title": "Instagram Reel (login required)",
            "creator": "Unknown",
            "channel_url": "",
            "follower_count": 0,
            "views": 0,
            "likes": 0,
            "comments": 0,
            "duration": 0,
            "upload_date": "N/A",
            "hashtags": [],
            "engagement_rate": 0.0,
            "transcript": "This Instagram Reel requires authentication to access. Metadata could not be retrieved.",
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