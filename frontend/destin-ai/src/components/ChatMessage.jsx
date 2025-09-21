import React from 'react';

const ChatMessage = ({ text, type }) => {
  return (
    <div className={`chat-message ${type}`}>
      {text}
    </div>
  );
};

export default ChatMessage;
