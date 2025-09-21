import React, { useState } from "react";
import axios from "axios";

const Chat = ({ user }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message locally
    const newMessages = [...messages, { text: input, sender: "user" }];
    setMessages(newMessages);
    setInput("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: input,
        history: [] // you can keep track if needed
      });

      setMessages((prev) => [...prev, { text: res.data.response, sender: "bot" }]);
    } catch (err) {
      setMessages((prev) => [...prev, { text: "Error: could not reach server.", sender: "bot" }]);
      console.error(err);
    }
  };

  return (
    <div className="chat-container">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`chat-message ${msg.sender === "user" ? "user" : "bot"}`}
        >
          {msg.text.split("\n").map((line, idx) => (
            <p key={idx}>{line}</p>
          ))}
        </div>
      ))}

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
