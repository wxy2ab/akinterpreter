import React from 'react';

interface Message {
  text: string;
  isBot: boolean;
}

const ChatMessage: React.FC<Message> = ({ text, isBot }) => (
  <div className={`p-2 ${isBot ? 'bg-gray-200' : 'bg-blue-200'} rounded-lg mb-2`}>
    <p>{isBot ? '🤖: ' : '你: '}{text}</p>
  </div>
);

export default ChatMessage;