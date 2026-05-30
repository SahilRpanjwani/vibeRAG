import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000/api",
});

export const ingestVideos = (urlA, urlB) =>
  API.post("/ingest", { url_a: urlA, url_b: urlB });

export const clearSession = (sessionId) =>
  API.delete(`/chat/${sessionId}`);

export const streamChat = (sessionId, question, onToken, onDone) => {
  fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  }).then(async (res) => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n").filter((l) => l.startsWith("data: "));

      for (const line of lines) {
        try {
          const json = JSON.parse(line.replace("data: ", ""));
          if (json.type === "token") onToken(json.content);
          if (json.type === "done") onDone(json.content);
        } catch {}
      }
    }
  });
};