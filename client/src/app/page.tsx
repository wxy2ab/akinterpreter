'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { getSession } from '../lib/api';

const ChatWindow = dynamic(() => import('../components/ChatWindow'), { ssr: false });
const MainWindow = dynamic(() => import('../components/MainWindow'), { ssr: false });

const Home: React.FC = () => {
    const [sessionData, setSessionData] = useState<any | null>(null);

    useEffect(() => {
        const fetchSession = async () => {
            const session = await getSession();
            setSessionData(session);
        };

        if (typeof window !== 'undefined') {
            fetchSession();
        }
    }, []);

    if (!sessionData) {
        return <div>Loading...</div>;
    }

    return (
        <div style={{ display: 'flex', height: '100vh' }}>
            <div style={{ flex: 1, borderRight: '1px solid #ccc' }}>
                <ChatWindow chatHistory={sessionData.chat_history} />
            </div>
            <div style={{ flex: 2, padding: '10px' }}>
                <MainWindow currentPlan={sessionData.current_plan} stepCodes={sessionData.step_codes} />
            </div>
        </div>
    );
};

export default Home;
