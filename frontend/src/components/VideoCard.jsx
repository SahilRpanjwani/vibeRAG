export default function VideoCard({ label, video, loading }) {
  if (loading) {
    return (
      <div className="video-card loading">
        <div className="card-label">Video {label}</div>
        <div className="skeleton-line" />
        <div className="skeleton-line short" />
        <div className="skeleton-line" />
      </div>
    );
  }

  if (!video) {
    return (
      <div className="video-card empty">
        <div className="card-label">Video {label}</div>
        <p className="empty-text">Paste a URL above to load video</p>
      </div>
    );
  }

  const embedUrl = video.platform === "youtube"
    ? `https://www.youtube.com/embed/${video.video_id}`
    : null;

  return (
    <div className="video-card">
      <div className="card-label">Video {label}</div>

      {embedUrl && (
        <iframe
          src={embedUrl}
          title={video.title}
          allowFullScreen
          className="video-embed"
        />
      )}

      <div className="video-info">
        <h3 className="video-title">{video.title}</h3>
        <p className="video-creator">by {video.creator}</p>

        <div className="stats-grid">
          <div className="stat">
            <span className="stat-label">Views</span>
            <span className="stat-value">{video.views?.toLocaleString()}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Likes</span>
            <span className="stat-value">{video.likes?.toLocaleString()}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Comments</span>
            <span className="stat-value">{video.comments?.toLocaleString()}</span>
          </div>
          <div className="stat highlight">
            <span className="stat-label">Engagement</span>
            <span className="stat-value">{video.engagement_rate}%</span>
          </div>
          <div className="stat">
            <span className="stat-label">Followers</span>
            <span className="stat-value">{video.follower_count?.toLocaleString()}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Duration</span>
            <span className="stat-value">{video.duration}s</span>
          </div>
        </div>
      </div>
    </div>
  );
}