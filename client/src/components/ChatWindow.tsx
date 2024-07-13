'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { getSession, getSessionId } from '../lib/api';

interface Message {
  type: string;
  content: any;
  isBot: boolean;
}

interface ChatWindowProps {
  chatHistory: Message[];
}

const ChatWindow: React.FC<ChatWindowProps> = ({ chatHistory }) => {
  const [messages, setMessages] = useState<Message[]>(chatHistory);
  const [isLoading, setIsLoading] = useState(false);
  const [appSessionId, setAppSessionId] = useState<string | null>(null);
  const messageBufferRef = useRef<Message | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    const fetchAppSessionId = async () => {
      const sessionId = await getSessionId();
      setAppSessionId(sessionId);
    };

    fetchAppSessionId();
  }, []);

  const handleSendMessage = useCallback(async (message: string) => {
    setMessages(prevMessages => [...prevMessages, { type: 'text', content: message, isBot: false }]);
    setIsLoading(true);
    messageBufferRef.current = null;

    try {
      const response = await fetch('/api/schat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: appSessionId, message }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const { session_id: chatSessionId } = await response.json();

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const eventSource = new EventSource(`/api/chat-stream?session_id=${chatSessionId}`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        const parsedData = JSON.parse(event.data);

        if (parsedData.type === 'text') {
          setMessages(prevMessages => {
            const newMessages = [...prevMessages];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.isBot && lastMessage.type === 'text') {
              lastMessage.content += parsedData.content;
              return [...newMessages.slice(0, -1), lastMessage];
            } else {
              return [...newMessages, { type: 'text', content: parsedData.content, isBot: true }];
            }
          });
        } else if (parsedData.type === 'error') {
          console.error(`Error: ${parsedData.content}`);
        } else if (parsedData.type === '[DONE]') {
          setIsLoading(false);
          eventSource.close();
        } else {
          setMessages(prevMessages => [
            ...prevMessages,
            { type: parsedData.type, content: parsedData.content, isBot: true }
          ]);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource failed:', error);
        eventSource.close();
        setIsLoading(false);
      };
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prevMessages => [
        ...prevMessages,
        { type: 'text', content: 'Error: Unable to get response from the server.', isBot: true }
      ]);
      setIsLoading(false);
    }
  }, [appSessionId]);

  return (
    <div className="flex flex-col h-full max-h-full">
      <div className="flex-grow overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <ChatMessage key={index} type={msg.type} content={msg.content} isBot={msg.isBot} />
        ))}
        {isLoading && <p className="italic text-gray-500">🤖在努力思考。。。</p>}
        <div ref={messagesEndRef} />
      </div>
      <div className="flex-shrink-0 p-4 border-t">
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

export default ChatWindow;
