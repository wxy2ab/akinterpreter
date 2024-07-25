import React, { useState, useEffect, useRef } from 'react';

const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<{type: string, content: string}[]>([]);
  const [input, setInput] = useState('');
  const eventSourceRef = useRef<EventSource | null>(null);

  const sendMessage = async () => {
    if (input.trim() === '') return;

    setMessages(prev => [...prev, { type: 'text', content: input }]);
    setInput('');

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    eventSourceRef.current = new EventSource(`/api/chat?message=${encodeURIComponent(input)}`);

    eventSourceRef.current.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSourceRef.current?.close();
        return;
      }

      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
    };

    eventSourceRef.current.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSourceRef.current?.close();
    };
  };

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  return (
    <div>
      <div style={{height: '300px', overflowY: 'scroll'}}>
        {messages.map((msg, index) => (
          <div key={index}>
            {msg.type === 'text' ? msg.content : JSON.stringify(msg)}
          </div>
        ))}
      </div>
      <input 
        type="text" 
        value={input} 
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
};

export default ChatComponent;