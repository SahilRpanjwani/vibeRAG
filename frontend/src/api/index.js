import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const API = axios.create({
  baseURL: `${BASE_URL}/api`,
});

export const ingestVideos = (urlA, urlB) =>
  API.post("/ingest", { url_a: urlA, url_b: urlB });

export const clearSession = (sessionId) =>
  API.delete(`/chat/${sessionId}`);

export const streamChat = (sessionId, question, onToken, onDone) => {
  fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  }).then(async (res) => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const json = JSON.parse(line.slice(6));
          if (json.type === "token") onToken(json.content);
          if (json.type === "done") onDone(json.content, json.citations || []);
        } catch {}
      }
    }
  });
};