import { useEffect, useRef, useState } from "react";
import "./App.css";

function getSessionId() {
  const key = "weather-advisory-session";
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = globalThis.crypto?.randomUUID?.() ?? `session-${Date.now()}`;
    sessionStorage.setItem(key, id);
  }
  return id;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(value = input, addUserMessage = true) {
    const message = value.trim();
    if (!message || loading) return;
    setInput("");
    setError("");
    if (addUserMessage)
      setMessages((items) => [...items, { role: "user", text: message }]);
    setLoading(true);
    try {
      const response = await fetch('/api/chat', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: getSessionId() }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(
          data.detail || "The advisory service could not answer right now.",
        );
      setMessages((items) => [
        ...items,
        { role: "assistant", text: data.response },
      ]);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the advisory service. Check that the backend is running and try again.",
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function startNewChat() {
    setMessages([]);
    setError("");
    sessionStorage.setItem(
      "weather-advisory-session",
      globalThis.crypto?.randomUUID?.() ?? `session-${Date.now()}`,
    );
    inputRef.current?.focus();
  }

  function onSubmit(event) {
    event.preventDefault();
    sendMessage();
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#home" aria-label="Skywise home">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32">
              <path d="M7.2 21.7a5.3 5.3 0 0 1 .7-10.5A8.5 8.5 0 0 1 24 9.8a6.1 6.1 0 0 1 .1 12.1H7.2Z" />
              <path d="m12.4 17.2 3.6-4 3.6 4M16 13.6v9" />
            </svg>
          </span>
          <span>
            weather-advisory-bot<span className="brand-period">.</span>
          </span>
        </a>
        <div className="topbar-right">
          <span className="service-status">
            <i />
            Weather assistant online
          </span>
          <button className="new-chat" type="button" onClick={startNewChat}>
            <span aria-hidden="true">+</span> New chat
          </button>
        </div>
      </header>

      <section
        className={`chat-layout ${messages.length ? "has-messages" : ""}`}
        aria-label="Weather advisory assistant"
      >
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="welcome-icon" aria-hidden="true">
              <svg viewBox="0 0 48 48">
                <path d="M13 32a7 7 0 0 1 .9-13.9 11 11 0 0 1 20.8-2A8 8 0 0 1 35 32H13Z" />
                <path d="M18 36h12M21 41h6" />
              </svg>
            </div>
            <p className="eyebrow">YOUR WEATHER, MADE CLEAR</p>
            <h1>
              Make plans with
              <br />
              <span>confidence.</span>
            </h1>
            <p className="welcome-copy">
              Ask about the weather and what it means for your day. Get
              practical advice for your plans, wherever you are.
            </p>
            
          </div>
        ) : (
          <div className="conversation" aria-live="polite">
            <div className="conversation-heading">
              <div>
                <p className="eyebrow">WEATHER ADVISORY</p>
                <h1>Your conversation</h1>
              </div>
              <span className="conversation-date">Live guidance</span>
            </div>
            <div className="message-list">
              {messages.map((message, index) => (
                <article
                  className={`message-row ${message.role}`}
                  key={`${index}-${message.role}`}
                >
                  <div className="avatar" aria-hidden="true">
                    {message.role === "assistant" ? (
                      <svg viewBox="0 0 24 24">
                        <path d="M5 16a4 4 0 0 1 .5-7.9 6.3 6.3 0 0 1 11.9-1.2 4.6 4.6 0 0 1 .1 9.1H5Z" />
                      </svg>
                    ) : (
                      "Y"
                    )}
                  </div>
                  <div className="message-content">
                    <span className="message-author">
                      {message.role === "assistant" ? "weather-advisory-bot" : "You"}
                    </span>
                    <div className="message-bubble">{message.text}</div>
                  </div>
                </article>
              ))}
              {loading && (
                <article className="message-row assistant">
                  <div className="avatar" aria-hidden="true">
                    <svg viewBox="0 0 24 24">
                      <path d="M5 16a4 4 0 0 1 .5-7.9 6.3 6.3 0 0 1 11.9-1.2 4.6 4.6 0 0 1 .1 9.1H5Z" />
                    </svg>
                  </div>
                  <div className="message-content">
                    <span className="message-author">weather-advisory-bot</span>
                    <div
                      className="message-bubble typing"
                      aria-label="Thinking"
                    >
                      <i />
                      <i />
                      <i />
                    </div>
                  </div>
                </article>
              )}
              {error && (
                <div className="error-note" role="alert">
                  <span aria-hidden="true">!</span>
                  <div>
                    <strong>Couldn�t get an advisory</strong>
                    <p>{error}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => sendMessage(messages.at(-1)?.text, false)}
                    disabled={loading}
                  >
                    Retry
                  </button>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>
        )}

        <div className="composer-wrap">
          <form className="composer" onSubmit={onSubmit}>
            <label className="sr-only" htmlFor="message-input">
              Ask about weather and your plans
            </label>
            <textarea
              id="message-input"
              ref={inputRef}
              rows="1"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Ask about weather and your plans�"
              disabled={loading}
            />
            <button
              className="send-button"
              type="submit"
              aria-label="Send message"
              disabled={!input.trim() || loading}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 19V5m-6 6 6-6 6 6" />
              </svg>
            </button>
          </form>
          <p className="composer-hint">
            This uses live weather and safety guidance <span>�</span> Enter
            to send
          </p>
        </div>
      </section>

      <footer className="footer">
        <span>Thoughtful weather guidance for everyday plans.</span>
        <span>
          Powered by live forecasts <i>�</i> Advice can�t replace official
          alerts
        </span>
      </footer>
    </main>
  );
}

export default App;

