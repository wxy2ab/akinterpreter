'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { getSession } from '../lib/api';

const ChatWindow = dynamic(() => import('../components/ChatWindow'), { ssr: false });
const MainWindow = dynamic(() => import('../components/MainWindow'), { ssr: false });
const SSEComponent = dynamic(() => import('../components/SSEComponent'), { ssr: false });

const Home: React.FC = () => {
    const [sessionData, setSessionData] = useState<any | null>(null);
    const [plan, setPlan] = useState<any>({});
    const [stepCodes, setStepCodes] = useState<{ [key: string]: string }>({});

    useEffect(() => {
        const fetchSession = async () => {
            const session = await getSession();
            setSessionData(session);
        };

        if (typeof window !== 'undefined') {
            fetchSession();
        }
    }, []);

    const handleSSEMessage = useCallback((data: { type: string; plan?: any; step_codes?: any }) => {
        if (data.type === 'plan') {
            setPlan(data.plan);
        } else if (data.type === 'code') {
            setStepCodes(data.step_codes);
        }
    }, []);

    if (!sessionData) {
        return <div>Loading...</div>;
    }

    return (
        <div style={{ display: 'flex', height: '100vh' }}>
            <div style={{ flex: 1, borderRight: '1px solid #ccc' }}>
                <ChatWindow chatHistory={sessionData.chat_history} />
                <SSEComponent sessionId={sessionData.session_id} onMessage={handleSSEMessage} />
            </div>
            <div style={{ flex: 2, padding: '10px' }}>
                <MainWindow currentPlan={plan} stepCodes={stepCodes} />
            </div>
        </div>
    );
};

export default Home;
