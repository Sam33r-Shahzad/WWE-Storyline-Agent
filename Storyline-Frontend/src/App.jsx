import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function newThreadId() {
  return `session-${Date.now()}`;
}

export default function App() {
  const [threadId] = useState(newThreadId);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Give me a feud, a match, or an event and I'll dig up what really happened, then reimagine it a different way.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [scripts, setScripts] = useState([]);
  const bottomRef = useRef(null);

  const loadScripts = async () => {
    try {
      const res = await fetch(`${API_BASE}/scripts`);
      const data = await res.json();
      setScripts(data.scripts || []);
    } catch {
      setScripts([]);
    }
  };

  useEffect(() => {
    loadScripts();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, thread_id: threadId }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply || "No reply came back." },
      ]);
      loadScripts();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Couldn't reach the backend. Is the server running on port 8000?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">WWE</span>
          <span className="brand-name">Scriptwriter</span>
        </div>

        <div className="sidebar-section">
          <h2>Saved scripts</h2>
          {scripts.length === 0 ? (
            <p className="empty">Nothing saved yet. Create something first.</p>
          ) : (
            <ul className="script-list">
              {scripts.map((name) => (
                <li key={name}>
                  <a href={`${API_BASE}/download/${name}`}>{name}</a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <main className="stage">
        <header className="stage-header">
          <h1>Tonight's Script</h1>
          <p>Research the history. Reimagine the outcome.</p>
        </header>

        <div className="chat">
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              <span className="label">
                {m.role === "user" ? "You" : "Scriptwriter"}
              </span>
              <p>{m.content}</p>
            </div>
          ))}
          {loading && (
            <div className="bubble assistant">
              <span className="label">Scriptwriter</span>
              <p className="thinking">Working the angle…</p>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="composer">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="e.g. Reimagine the ending of WrestleMania 30, The Undertaker vs. Brock Lesnar"
            rows={2}
          />
          <button onClick={send} disabled={loading || !input.trim()}>
            Reimagine it
          </button>
        </div>
      </main>
    </div>
  );
}
