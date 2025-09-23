import { useState, useCallback } from "react";
import { nanoid } from "nanoid/non-secure";

const createEmptyChat = (title = "New chat") => ({
  id: nanoid(),
  title,
  messages: [{ sender: "bot", text: "Hello 👋 I’m Querion your AI assistant." }]
});

export default function useChat() {
  const [chats, setChats] = useState([createEmptyChat("Welcome")]);
  const [activeId, setActiveId] = useState(chats[0].id);
  const [input, setInput] = useState("");
  const [persona, setPersona] = useState("Tutor");
  const [model, setModel] = useState("Chat");

  const activeChat = chats.find(c => c.id === activeId) || chats[0];

  const setActiveChatMessages = useCallback((updater) => {
    setChats(prev => prev.map(c => c.id === activeChat.id ? { ...c, messages: typeof updater === 'function' ? updater(c.messages) : updater } : c));
  }, [activeChat && activeChat.id]);

  const sendMessage = (text, sender = "user") => {
    if (!text.trim()) return;

    const newMessage = { sender, text };
    if (sender === "user") {
      setInput("");
    }
    setActiveChatMessages(prev => [...prev, newMessage]);
  };

  const newChat = (title) => {
    const chat = createEmptyChat(title || "New chat");
    setChats(prev => [chat, ...prev]);
    setActiveId(chat.id);
  };

  const selectChat = (id) => setActiveId(id);

  const deleteChat = (id) => {
    setChats(prev => prev.filter(c => c.id !== id));
    if (activeId === id && chats.length > 1) {
      setActiveId(chats.find(c => c.id !== id).id);
    }
  };

  const renameChat = (id, title) => {
    setChats(prev => prev.map(c => c.id === id ? { ...c, title } : c));
  };

  return {
    chats,
    activeChat,
    input,
    setInput,
    persona,
    setPersona,
    model,
    setModel,
    sendMessage,
    newChat,
    selectChat,
    deleteChat,
    renameChat
  };
}
