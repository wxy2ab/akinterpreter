'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

interface Message {
  text: string;
  isBot: boolean;
}

const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const currentBotMessageRef = useRef('');

  const handleSendMessage = useCallback(async (message: string) => {
    setMessages(prevMessages => [...prevMessages, { text: message, isBot: false }]);
    setIsLoading(true);
    currentBotMessageRef.current = '';

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const { session_id } = await response.json();

      if (eventSource) {
        eventSource.close();
      }

      const newEventSource = new EventSource(`/api/chat-stream?session_id=${session_id}`);
      setEventSource(newEventSource);

      newEventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          setIsLoading(false);
          newEventSource.close();
          return;
        }

        try {
          const parsed = JSON.parse(event.data);
          if (parsed.type === 'text') {
            currentBotMessageRef.current += parsed.content;
            setMessages(prevMessages => {
              const newMessages = [...prevMessages];
              if (newMessages.length > 0 && newMessages[newMessages.length - 1].isBot) {
                newMessages[newMessages.length - 1].text = currentBotMessageRef.current;
              } else {
                newMessages.push({ text: currentBotMessageRef.current, isBot: true });
              }
              return newMessages;
            });
          }
        } catch (e) {
          console.error('Error parsing SSE data', e);
        }
      };

      newEventSource.onerror = (error) => {
        console.error('EventSource failed:', error);
        newEventSource.close();
        setIsLoading(false);
      };
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prevMessages => [...prevMessages, { text: 'Error: Unable to get response from the server.', isBot: true }]);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return (
    <div className="flex flex-col h-[400px] border rounded p-4">
      <div className="flex-grow overflow-y-auto mb-4">
        {messages.map((msg, index) => (
          <ChatMessage key={index} text={msg.text} isBot={msg.isBot} />
        ))}
        {isLoading && <p className="italic text-gray-500">Bot is typing...</p>}
      </div>
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  );
};

export default ChatWindow;