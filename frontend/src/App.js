import React, { useState, useEffect } from "react";
import ChatWindowFree from "./ChatWindowFree";
import ChatWindowPro from "./ChatWindowPro";
import useChat from "./useChat";
import Login from "./Login";

import "./App.css";

export default function App() {
  // persist version across reloads
  const [version, setVersion] = useState(() => {
    try {
      return localStorage.getItem('appVersion') || 'Free';
    } catch (e) {
      return 'Free';
    }
  });
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState(null);

  // set a CSS variable with the inner height to handle mobile browser UI and ensure
  // the chat container fits without page scrolling
  useEffect(() => {
    const storedUserId = localStorage.getItem('user_id');
    if (storedUserId) {
      setIsLoggedIn(true);
      setUserId(storedUserId);
    }
  }, []);

  const chat = useChat(userId);

  const handleLogin = (id) => {
    setIsLoggedIn(true);
    setUserId(id);
  };

  const handleLogout = () => {
    (async () => {
      try {
        if (userId) {
          // Request server to purge user vectors on logout
          const resp = await fetch(`http://localhost:8000/logout/?user_id=${userId}&purge=true`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });
          if (!resp.ok) {
            console.error('Server failed to clear user vectors on logout', await resp.text());
            // Notify user but still proceed to clear client session
            alert('Could not clear uploaded files on the server while logging out. Please try again or contact support.');
          }
        }
      } catch (err) {
        console.error('Logout request failed', err);
        alert('Could not reach the server to clear uploaded files. You will be logged out locally.');
      } finally {
        localStorage.removeItem('user_id');
        // Keep the selected version persisted across reloads, do not clear it on logout
        setIsLoggedIn(false);
        setUserId(null);
      }
    })();
  };

  // keep version synced to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('appVersion', version);
    } catch (e) {
      // ignore
    }
  }, [version]);

  // switch favicon depending on Free/Pro
  useEffect(() => {
    try {
      const favicon = document.querySelector("link[rel~='icon']");
      const free = '/querion free.ico';
      const pro = '/querion pro.ico';
      if (favicon) {
        favicon.href = version === 'Pro' ? pro : free;
      } else {
        const link = document.createElement('link');
        link.rel = 'icon';
        link.href = version === 'Pro' ? pro : free;
        document.head.appendChild(link);
      }
    } catch (e) {
      // ignore
    }
  }, [version]);

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
            <button className="logout-btn" onClick={handleLogout}>Logout</button>
          </div>

          <div className="app-inner">
            {/* Promo for Free users */}
            {version === 'Free' && (
              <div className="pro-promo" role="note" aria-live="polite">
                Take our Pro Subscription for smarter responses and exciting new Features
              </div>
            )}
            <aside className="sidebar">
              <div className="sidebar-header">
                <button className="new-chat-btn" onClick={() => chat.newChat()}>+ New chat</button>
              </div>
              <div className="chat-list">
                {chat.chats.map(c => (
                  <div key={c.id} className={`chat-list-item ${chat.activeChat.id === c.id ? 'active' : ''}`}>
                    <div className="chat-list-main" onClick={() => chat.selectChat(c.id)}>
                      <div className="chat-list-title">{c.title.length > 30 ? `${c.title.substring(0, 30)}...` : c.title}</div>
                      <div className="chat-list-meta">{c.messages.length} messages</div>
                    </div>
                    <div className="chat-list-actions">
                      <button title={c.pinned ? 'Unpin' : 'Pin'} onClick={() => chat.togglePin(c.id)}>{c.pinned ? '📌' : '📍'}</button>
                      <button title="Delete" onClick={() => { if(window.confirm('Delete this chat?')) chat.deleteChat(c.id); }}>🗑️</button>
                    </div>
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
