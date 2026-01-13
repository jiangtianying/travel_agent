import { useState, useEffect, useRef } from "react";
import type { Message } from "./types";
import { sendMessage, resetSession, getModels, changeModel } from "./api";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [currentModel, setCurrentModel] = useState("");
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadModels = async () => {
    try {
      const data = await getModels();
      setModels(data.models);
      setCurrentModel(data.current_model);
    } catch (error) {
      console.error("Failed to load models:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendMessage(input, sessionId);
      const assistantMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetSession(sessionId);
      setMessages([]);
    } catch (error) {
      console.error("Failed to reset session:", error);
    }
  };

  const handleModelChange = async (model: string) => {
    try {
      await changeModel(model);
      setCurrentModel(model);
    } catch (error) {
      console.error("Failed to change model:", error);
    }
  };

  const examplePrompts = [
    "I want to plan a 7-day trip to Paris in April with a budget of $2000",
    "Help me find flights from New York to London for next month",
    "Plan a romantic getaway in Italy for 5 days",
    "I need a business trip itinerary for 3 days in Singapore",
  ];

  return (
    <div className="app">
      <header className="header">
        <h1>Travel Agent AI</h1>
        <p>Your personal travel planning assistant</p>
      </header>

      <div className="controls">
        <div className="model-selector">
          <label className="model-label">Model Selection</label>
          <select
            value={currentModel}
            onChange={(e) => handleModelChange(e.target.value)}
            className="model-select"
            disabled={models.length === 0}
          >
            {models.length === 0 ? (
              <option value="">Loading...</option>
            ) : (
              models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))
            )}
          </select>
        </div>
        <button onClick={handleReset} className="reset-btn">
          Clear Chat
        </button>
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome!</h2>
              <p>I can help you plan your perfect trip. Tell me where you want to go!</p>
              <div className="examples">
                <p>Try one of these:</p>
                {examplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(prompt)}
                    className="example-btn"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-content">
                <span className="role">{msg.role === "user" ? "You" : "Assistant"}</span>
                <div className="text">
                  {msg.role === "assistant" ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <span className="role">Assistant</span>
                <div className="text loading">Thinking...</div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tell me about your travel plans..."
            disabled={isLoading}
            className="message-input"
          />
          <button type="submit" disabled={isLoading || !input.trim()} className="send-btn">
            {isLoading ? "Sending..." : "Send"}
          </button>
        </form>
      </div>

      <footer className="footer">
        <p>
          Traces available at{" "}
          <a href="https://platform.openai.com/traces" target="_blank" rel="noopener noreferrer">
            OpenAI Traces Dashboard
          </a>{" "}
          (workflow: travel_agent)
        </p>
      </footer>
    </div>
  );
}

export default App;
