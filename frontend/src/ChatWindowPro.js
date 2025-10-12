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
      body: JSON.stringify({ query: input, user_id: userId, version: "Pro", model }),
    });
    const data = await response.json();
    sendMessage(data.response, "bot");

  };

  return (
    <div className="chat-container chat-pro">
      <div className="chat-header chat-pro">
        <div className="logo chat-pro">
          <img src="/querion pro.ico" alt="Querion Pro" className="brand-avatar" /> Querion (Pro)
        </div>
        <div className="model-select">
          <select value={model} onChange={e => setModel(e.target.value)}>
            <option value="nvidia/llama3-chatqa-1.5-70b">llama3-chatqa-1.5-70b (default)</option>
            <option value="speakleash/bielik-11b-v2.6-instruct">bielik-11b-v2.6-instruct</option>
            <option value="speakleash/bielik-11b-v2.3-instruct">bielik-11b-v2.3-instruct</option>            
            <option value="thudm/chatglm3-6b">chatglm3-6b</option>
            <option value="meta/llama-3.1-405b-instruct">llama-3.1-405b-instruct</option>
            <option value="nvidia/llama3-chatqa-1.5-8b">llama3-chatqa-1.5-8b(Free)</option>            
            <option value="mediatek/breeze-7b-instruct">breeze-7b-instruct(Chinese)</option>
          </select>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          msg.sender === 'bot' ? (
            <div key={i} className={`message bot chat-pro`}>
              <img src="/querion pro.ico" alt="Querion Pro" className="avatar" />
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

        <div className="file-group">
          <input id="pro-file-input" type="file" onChange={handleFileChange} style={{ display: 'none' }} />
          <label htmlFor="pro-file-input" className="file-button">Choose</label>
          <div className="file-name" title={fileName}>{fileName ? (fileName.length > 40 ? fileName.slice(0, 37) + '...' : fileName) : 'No file'}</div>
        </div>

        

        <div className="actions">
          <button className="upload-button" onClick={handleFileUpload}>Upload</button>
          <button className="chat-pro-send" onClick={() => handleSendMessage()}>Send</button>
        </div>
      </div>
    </div>
  );
}
