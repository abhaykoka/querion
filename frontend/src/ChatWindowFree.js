import React from "react";
import "./App.css";      // global styles
import "./AppFree.css";  // Free-specific overrides

export default function ChatWindowFree(props) {
  const { activeChat, input, setInput, persona, setPersona, model, setModel, sendMessage, userId } = props;
  const messages = activeChat ? activeChat.messages : [];

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    sendMessage(input);
    const response = await fetch("http://localhost:8000/query/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: input, user_id: userId, version: "Free" }),
    });
    const data = await response.json();
    sendMessage(data.response, "bot");

  };

  return (
    <div className="chat-container chat-free">
      <div className="chat-header chat-free">
        <div className="logo chat-free">
          <img src="/Querion%20Logo.png" alt="Querion" className="brand-avatar" /> Querion (Free)
        </div>
        <div className="controls">
          <select className="persona-select" value={persona} onChange={e => setPersona(e.target.value)}>
            {["Tutor","Dev","Friendly","Concise","Pro"].map(p => <option key={p}>{p}</option>)}
          </select>
          <select className="persona-select" value={model} onChange={e => setModel(e.target.value)}>
            {["Chat","Image"].map(m => <option key={m}>{m}</option>)}
          </select>
        </div>
      </div>

      <div className="chat-messages">
  {messages.map((msg, i) => (
          msg.sender === 'bot' ? (
            <div key={i} className={`message bot chat-free`}>
              <img src="/Querion%20Logo.png" alt="Querion" className="avatar" />
              <div className={`chat-bubble ${msg.sender} chat-free`}>
                {msg.text}
              </div>
            </div>
          ) : (
            <div key={i} className={`message user chat-free`}>
              <div className={`chat-bubble ${msg.sender} chat-free`}>
                {msg.text}
              </div>
            </div>
          )
        ))}
      </div>

      <div className="chat-input">
        <input
          type="text"
          placeholder="Bring your thoughts to life ..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSendMessage()}
        />
        <button onClick={() => handleSendMessage()}>Send</button>
      </div>
    </div>
  );
}