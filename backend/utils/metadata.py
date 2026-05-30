def compute_engagement_rate(likes: int, comments: int, views: int) -> float:
    if views == 0:
        return 0.0
    return round((likes + comments) / views * 100, 4)