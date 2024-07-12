import React, { useEffect } from 'react';

interface SSEComponentProps {
    sessionId: string;
    onMessage: (data: { plan: any; step_codes: any }) => void;
}

const SSEComponent: React.FC<SSEComponentProps> = ({ sessionId, onMessage }) => {
    useEffect(() => {
        const eventSource = new EventSource(`/api/sse?session_id=${sessionId}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        eventSource.onerror = (error) => {
            console.error('EventSource failed:', error);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId, onMessage]);

    return null;
};

export default SSEComponent;
