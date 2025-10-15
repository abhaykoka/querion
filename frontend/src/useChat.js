import { useState, useCallback, useEffect } from "react";
import { nanoid } from "nanoid/non-secure";

const DEFAULT_BOT = { sender: "bot", text: "Hello 👋 I’m Querion your AI assistant." };
const createEmptyChat = (title = "New chat") => ({
  id: nanoid(),
  title,
  pinned: false,
  createdAt: Date.now(),
  messages: [DEFAULT_BOT]
});

export default function useChat(userId) {
  const storageKey = `querion_chats_${userId ?? 'anon'}`;
  const activeKey = `querion_active_${userId ?? 'anon'}`;

  const [chats, setChats] = useState(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) return JSON.parse(raw);
    } catch (e) {
      // ignore
    }
    return [createEmptyChat('Welcome')];
  });

  const [activeId, setActiveId] = useState(() => {
    try {
      const a = localStorage.getItem(activeKey);
      if (a) return a;
    } catch (e) {}
    return null;
  });

  const [input, setInput] = useState("");
  const [persona, setPersona] = useState("Tutor");
  const [model, setModel] = useState("meta/llama-3.1-405b-instruct");
  const [agentMode, setAgentMode] = useState(() => {
    try {
      const v = localStorage.getItem(`${storageKey}_agentMode`);
      return v ? JSON.parse(v) : false;
    } catch (e) {
      return false;
    }
  });

  // Ensure there's always an activeId
  useEffect(() => {
    if (!activeId && chats.length > 0) {
      setActiveId(chats[0].id);
    }
  }, [activeId, chats]);

  // If userId changes, reload from the corresponding storage keys
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) setChats(JSON.parse(raw));
      const a = localStorage.getItem(activeKey);
      if (a) setActiveId(a);
    } catch (e) {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // Persist chats and activeId to localStorage whenever they change
  useEffect(() => {
    try {
      // avoid writing immediately on first render when chats may be placeholder
      if (!chats) return;
      localStorage.setItem(storageKey, JSON.stringify(chats));
      if (activeId) localStorage.setItem(activeKey, activeId);
      localStorage.setItem(`${storageKey}_agentMode`, JSON.stringify(agentMode));
    } catch (e) {
      // ignore storage errors
    }
  }, [chats, activeId, storageKey, activeKey]);

  // Keep pinned chats at the front (stable sort)
  const sortedChats = chats.slice().sort((a, b) => {
    if (a.pinned === b.pinned) return b.createdAt - a.createdAt; // newest first
    return (a.pinned ? -1 : 1);
  });

  const activeChat = sortedChats.find(c => c.id === activeId) || sortedChats[0];

  const setActiveChatMessages = useCallback((updater) => {
    setChats(prev => prev.map(c => c.id === activeChat.id ? { ...c, messages: typeof updater === 'function' ? updater(c.messages) : updater } : c));
  }, [activeChat && activeChat.id]);

  // When a user sends the first message in a new chat, use that message to name the chat
  const sendMessage = (text, sender = "user") => {
    if (!text.trim()) return;

    const newMessage = { sender, text };
    if (sender === "user") {
      setInput("");
    }

    setChats(prev => prev.map(c => {
      if (c.id !== activeChat.id) return c;
      const nextMessages = [...c.messages, newMessage];
      let nextTitle = c.title;
      // Auto-name if the chat only had the default bot message before this user message
      if (c.messages.length <= 1 && c.title && (c.title === 'New chat' || c.title === 'Welcome' || c.title.startsWith('New'))) {
        const candidate = text.trim().split('\n')[0].slice(0, 30);
        nextTitle = candidate || c.title;
      }
      return { ...c, messages: nextMessages, title: nextTitle };
    }));
  };

  const newChat = (title) => {
    const chat = createEmptyChat(title || "New chat");
    setChats(prev => [chat, ...prev]);
    setActiveId(chat.id);
  };

  const selectChat = (id) => {
    setActiveId(id);
  };

  const deleteChat = async (id) => {
    try {
      const response = await fetch(`http://localhost:8000/delete_chat/?user_id=${userId}&chat_id=${id}`, {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        alert(data.detail);
        return;
      }
    } catch (error) {
      console.error("Failed to delete chat on the server:", error);
      // Optionally, you can choose to not proceed with deleting the chat from the local state
      // if the server-side deletion fails.
    }

    setChats(prev => {
      const next = prev.filter(c => c.id !== id);
      return next.length ? next : [createEmptyChat('Welcome')];
    });
    setActiveId(prev => (prev === id ? null : prev));
  };

  const renameChat = (id, title) => {
    setChats(prev => prev.map(c => c.id === id ? { ...c, title } : c));
  };

  const togglePin = (id) => {
    setChats(prev => prev.map(c => c.id === id ? { ...c, pinned: !c.pinned, createdAt: Date.now() } : c));
  };

  return {
    chats: sortedChats,
    activeChat,
    input,
    setInput,
    persona,
    setPersona,
    model,
    setModel,
    agentMode,
    setAgentMode,
    sendMessage,
    newChat,
    selectChat,
    deleteChat,
    renameChat,
    togglePin
  };
}
