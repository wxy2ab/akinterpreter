import React, { useState, useEffect, useRef } from 'react';
import { getSessionId } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatWindowProps {
  initialMessages?: Message[];
}

const ChatWindow: React.FC<ChatWindowProps> = ({ initialMessages = [] }) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    getSessionId().then(setSessionId);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (sessionId) {
      eventSourceRef.current = new EventSource(`/api/sse?session_id=${sessionId}`);
      
      eventSourceRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'chat_history') {
          // Handle special updates like resetting or clearing history
          setMessages(data.chat_history);
        }
      };

      eventSourceRef.current.onerror = (error) => {
        console.error('EventSource failed:', error);
      };

      return () => {
        eventSourceRef.current?.close();
      };
    }
  }, [sessionId]);

  const sendMessage = async (message: string) => {
    if (!message.trim() || !sessionId) return;

    const newUserMessage: Message = { role: 'user', content: message };
    setMessages(prev => [...prev, newUserMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/schat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId, message }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      let assistantMessage: Message = { role: 'assistant', content: '' };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n').filter(line => line.trim() !== '');
        
        for (const line of lines) {
          const data = JSON.parse(line);
          if (data.type === 'text') {
            assistantMessage.content += data.content;
            setMessages(prev => [
              ...prev.slice(0, -1),
              { ...prev[prev.length - 1] },
              { ...assistantMessage }
            ]);
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Unable to get response from the server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessages = () => {
    return messages.map((message, index) => (
      <div
        key={index}
        style={{
          marginBottom: '10px',
          padding: '10px',
          borderRadius: '5px',
          backgroundColor: message.role === 'assistant' ? '#4a5568' : '#3182ce',
          color: 'white',
          maxWidth: '80%',
          alignSelf: message.role === 'assistant' ? 'flex-start' : 'flex-end'
        }}
      >
        {message.content}
      </div>
    ));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '100vh', backgroundColor: '#1a202c', color: 'white' }}>
      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '20px' }}>
        {renderMessages()}
        {isLoading && <div style={{ color: '#a0aec0', fontStyle: 'italic' }}>AI is thinking...</div>}
        <div ref={messagesEndRef} />
      </div>
      <div style={{ padding: '20px', borderTop: '1px solid #4a5568', display: 'flex' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage(input)}
          style={{
            flexGrow: 1,
            padding: '10px',
            borderRadius: '5px 0 0 5px',
            border: '1px solid #4a5568',
            backgroundColor: '#2d3748',
            color: 'white'
          }}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={isLoading}
          style={{
            padding: '10px 20px',
            borderRadius: '0 5px 5px 0',
            border: '1px solid #4a5568',
            backgroundColor: '#3182ce',
            color: 'white',
            cursor: 'pointer',
            opacity: isLoading ? 0.5 : 1
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;