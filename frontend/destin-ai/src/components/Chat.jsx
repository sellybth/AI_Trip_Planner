import React, { useState } from "react";
import axios from "axios";
import ChatMessage from "./ChatMessage";

const Chat = ({ user }) => {
  const [messages, setMessages] = useState([]); 
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newUserMessage = { role: "user", parts: [{ text: input }] };

    // Optimistically render user message
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");

    try {
      const formattedHistory = messages.map((msg) => ({
        role: msg.role,
        parts: msg.parts.map((part) =>
          part.text ? { text: part.text } : part
        ),
      }));

      const historyToSend = [...formattedHistory, newUserMessage];

      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: input,
        history: historyToSend,
      });

      const botResponse = res.data.response;

      // 🔑 Wrap bot response so it always fits the format
      const newBotMessage = { role: "model", parts: [{ text: botResponse }] };

      setMessages((prev) => [...prev, newBotMessage]);
    } catch (err) {
      console.error("Error sending message:", err);
      setMessages((prev) => [
        ...prev,
        { role: "model", parts: [{ text: "❌ Error: Could not get a response." }] },
      ]);
    }
  };

  return (
    <div className="chat-container">
      
      <div className="chat-history-display">
        
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} parts={msg.parts} />
        ))}
      </div>

      <div className="input-container">
        <input
          type="text"
          placeholder="Ask DestinAI..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chat;
