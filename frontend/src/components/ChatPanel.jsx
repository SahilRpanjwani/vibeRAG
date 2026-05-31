    import { useState, useRef, useEffect } from "react";
    import { streamChat, clearSession } from "../api/index.js";
    import ReactMarkdown from "react-markdown";

    export default function ChatPanel({ ready, sessionId }) {
      const [messages, setMessages] = useState([]);
      const [input, setInput] = useState("");
      const [streaming, setStreaming] = useState(false);
      const bottomRef = useRef(null);

      useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      }, [messages]);

      const sendMessage = () => {
        if (!input.trim() || streaming || !ready) return;

        const question = input.trim();
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: question }]);
        setStreaming(true);

        // Add empty assistant message to stream into
        setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true }]);

    streamChat(
      sessionId,
      question,
(token) => {
    if (!token) return;
    setMessages((prev) => {
      const updated = prev.map((msg, i) =>
        i === prev.length - 1
          ? { ...msg, content: msg.content + token }
          : msg
      );
      return updated;
    });
  },
    (_, citations) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].citations = citations;
          updated[updated.length - 1].streaming = false;
          return updated;
        });
        setStreaming(false);
      }
    );
      };

      const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      };

      const handleClear = () => {
        clearSession(sessionId);
        setMessages([]);
      };

const suggestions = [
    "Which video had better engagement and why?",
    "Compare the hooks in the first 5 seconds",
    "What's the engagement rate of each video?",
    "How can the lower performing video improve?",
];

      return (
        <div className="chat-panel">
          <div className="chat-header">
            <span>AI Analysis</span>
            {messages.length > 0 && (
              <button className="clear-btn" onClick={handleClear}>Clear</button>
            )}
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="suggestions">
                <p className="suggestions-title">Try asking:</p>
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    className="suggestion-chip"
                    onClick={() => setInput(s)}
                    disabled={!ready}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

    {messages.map((msg, i) => (
      <div key={i} className={`message ${msg.role}`}>
     <div className="message-bubble">
      {msg.streaming
        ? msg.content
        : <ReactMarkdown>{msg.content}</ReactMarkdown>}
    </div>
        {msg.citations && msg.citations.length > 0 && (
          <div className="citations">
            {msg.citations.map((c, j) => (
              <span key={j} className="citation-chip">
                Video {c.video_id} · chunk {c.chunk_index}
              </span>
            ))}
          </div>
        )}
      </div>
    ))}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row">
            <textarea
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={ready ? "Ask about the videos..." : "Ingest videos first..."}
              disabled={!ready || streaming}
              rows={2}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={!ready || streaming || !input.trim()}
            >
              {streaming ? "..." : "Send"}
            </button>
          </div>
        </div>
      );
    }