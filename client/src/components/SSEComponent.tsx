import React, { useEffect, useState } from 'react';

interface SSEComponentProps {
    sessionId: string;
}

const SSEComponent: React.FC<SSEComponentProps> = ({ sessionId }) => {
    const [messages, setMessages] = useState<string[]>([]);

    useEffect(() => {
        const eventSource = new EventSource(`/api/sse?session_id=${sessionId}`);

        eventSource.onmessage = (event) => {
            setMessages((prevMessages) => [...prevMessages, event.data]);
        };

        eventSource.onerror = (error) => {
            console.error('EventSource failed:', error);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId]);

    return (
        <div>
            <h1>SSE Messages</h1>
            <ul>
                {messages.map((msg, index) => (
                    <li key={index}>{msg}</li>
                ))}
            </ul>
        </div>
    );
};

export default SSEComponent;
