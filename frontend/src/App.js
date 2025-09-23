import React, { useState, useEffect } from "react";
import ChatWindowFree from "./ChatWindowFree";
import ChatWindowPro from "./ChatWindowPro";
import useChat from "./useChat";
import Login from "./Login";

import "./App.css";

export default function App() {
  const [version, setVersion] = useState("Free");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState(null);

  // set a CSS variable with the inner height to handle mobile browser UI and ensure
  // the chat container fits without page scrolling
  useEffect(() => {
    const setHeight = () => {
      document.documentElement.style.setProperty('--app-inner-height', window.innerHeight + 'px');
    };
    setHeight();
    window.addEventListener('resize', setHeight);
    return () => window.removeEventListener('resize', setHeight);
  }, []);

  const chat = useChat();

  const handleLogin = (id) => {
    setIsLoggedIn(true);
    setUserId(id);
  };

  return (
    <div className={`app-root ${version === "Pro" ? 'is-pro' : 'is-free'}`}>
      {!isLoggedIn ? (
        <Login onLogin={handleLogin} />
      ) : (
        <>
          <div className="version-select-wrapper">
            <label>Select Version: </label>
            <select
              value={version}
              onChange={(e) => setVersion(e.target.value)}
            >
              <option>Free</option>
              <option>Pro</option>
            </select>
          </div>

          <div className="app-inner">
            <aside className="sidebar">
              <div className="sidebar-header">
                <button className="new-chat-btn" onClick={() => chat.newChat()}>+ New chat</button>
              </div>
              <div className="chat-list">
                {chat.chats.map(c => (
                  <div key={c.id} className={`chat-list-item ${chat.activeChat.id === c.id ? 'active' : ''}`} onClick={() => chat.selectChat(c.id)}>
                    <div className="chat-list-title">{c.title}</div>
                    <div className="chat-list-meta">{c.messages.length} messages</div>
                  </div>
                ))}
              </div>
            </aside>

            <main className="main-panel">
              {version === "Free" ? (
                <ChatWindowFree {...chat} userId={userId} />
              ) : (
                <ChatWindowPro {...chat} userId={userId} />
              )}
            </main>
          </div>
        </>
      )}
    </div>
  );
}
