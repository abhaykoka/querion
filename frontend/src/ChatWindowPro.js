import React, { useState } from "react";
import "./App.css";      // global styles
import "./AppPro.css";   // Pro-specific overrides

export default function ChatWindowPro(props) {
  const { activeChat, input, setInput, persona, setPersona, model, setModel, sendMessage, userId } = props;
  const messages = activeChat ? activeChat.messages : [];
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setFileName(selectedFile ? selectedFile.name : "");
  };

  const handleFileUpload = async () => {
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`http://localhost:8000/uploadfile/?user_id=${userId}`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (response.ok) {
      alert("File uploaded successfully.");
    } else {
      alert(data.detail);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    sendMessage(input);
    const response = await fetch("http://localhost:8000/query/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: input, user_id: userId, version: "Pro" }),
    });
    const data = await response.json();
    sendMessage(data.response, "bot");

  };

  return (
    <div className="chat-container chat-pro">
      <div className="chat-header chat-pro">
        <div className="logo chat-pro">
          <img src="/Querion%20Logo.png" alt="Querion" className="brand-avatar" /> Querion (Pro)
        </div>
        
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          msg.sender === 'bot' ? (
            <div key={i} className={`message bot chat-pro`}>
              <img src="/Querion%20Logo.png" alt="Querion" className="avatar" />
              <div className={`chat-bubble ${msg.sender} chat-pro`}>
                {msg.text}
              </div>
            </div>
          ) : (
            <div key={i} className={`message user chat-pro`}>
              <div className={`chat-bubble ${msg.sender} chat-pro`}>
                {msg.text}
              </div>
            </div>
          )
        ))}
      </div>

      <div className="chat-input">
        <input
          type="text"
          placeholder="⚡Bring your thoughts to life..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSendMessage()}
        />
        <button className="chat-pro-send" onClick={() => handleSendMessage()}>Send</button>
        <input type="file" onChange={handleFileChange} />
        {fileName && <span style={{color: 'black'}}>{fileName}</span>}
        <button onClick={handleFileUpload}>Upload</button>
      </div>
    </div>
  );
}
