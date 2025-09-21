import React from "react";
import ReactMarkdown from "react-markdown";
import "../App.css"; // Make sure you import your CSS

const ChatMessage = ({ role, parts }) => {
  return (
    <div className={`chat-message ${role === "user" ? "user" : "bot"}`}>
      {parts.map((part, i) => {
        if (part.text) {
          return (
            <div key={i} className="message-bubble">
              <ReactMarkdown>{part.text}</ReactMarkdown>
            </div>
          );
        }
        if (part.function_call) {
          return (
            <div key={i} className="function-call">
              <strong>🛠 Function call:</strong> {part.function_call.name}
              <pre>{JSON.stringify(part.function_call.args, null, 2)}</pre>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
};

export default ChatMessage;
