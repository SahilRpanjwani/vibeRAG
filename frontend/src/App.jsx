import { useState, useRef } from "react";
import { ingestVideos } from "./api/index.js";
import VideoCard from "./components/VideoCard.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import "./App.css";

const SESSION_ID = "session-" + Math.random().toString(36).slice(2);

export default function App() {
  const [urlA, setUrlA] = useState("");
  const [urlB, setUrlB] = useState("");
  const [videoA, setVideoA] = useState(null);
  const [videoB, setVideoB] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);

  const handleIngest = async () => {
    if (!urlA.trim() || !urlB.trim()) {
      setError("Please enter both video URLs.");
      return;
    }
    setError("");
    setLoading(true);
    setReady(false);
    setVideoA(null);
    setVideoB(null);

    try {
      const res = await ingestVideos(urlA.trim(), urlB.trim());
      setVideoA(res.data.video_a);
      setVideoB(res.data.video_b);
      setReady(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to ingest videos. Check the URLs and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">vibeRAG</h1>
        <p className="app-subtitle">AI-powered social media video analysis</p>
      </header>

      <section className="url-section">
        <div className="url-inputs">
          <div className="url-field">
            <label>Video A — YouTube</label>
            <input
              type="text"
              value={urlA}
              onChange={(e) => setUrlA(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              disabled={loading}
            />
          </div>
          <div className="url-field">
            <label>Video B — Instagram Reel</label>
            <input
              type="text"
              value={urlB}
              onChange={(e) => setUrlB(e.target.value)}
              placeholder="https://www.instagram.com/reel/..."
              disabled={loading}
            />
          </div>
        </div>

        <button
          className="ingest-btn"
          onClick={handleIngest}
          disabled={loading}
        >
          {loading ? "Analyzing..." : "Analyze Videos"}
        </button>

        {error && <p className="error-msg">{error}</p>}
      </section>

      <section className="videos-section">
        <VideoCard label="A" video={videoA} loading={loading} />
        <VideoCard label="B" video={videoB} loading={loading} />
      </section>

      <section className="chat-section">
        <ChatPanel ready={ready} sessionId={SESSION_ID} />
      </section>
    </div>
  );
}