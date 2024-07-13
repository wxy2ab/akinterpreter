'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { getSession } from '../lib/api';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';

const ChatWindow = dynamic(() => import('../components/ChatWindow'), { ssr: false });
const MainWindow = dynamic(() => import('../components/MainWindow'), { ssr: false });
const SSEComponent = dynamic(() => import('../components/SSEComponent'), { ssr: false });

const Home: React.FC = () => {
    const [sessionData, setSessionData] = useState<any | null>(null);
    const [plan, setPlan] = useState<any>({});
    const [stepCodes, setStepCodes] = useState<{ [key: string]: string }>({});
    const [chatHistory, setChatHistory] = useState<any[]>([]);

    useEffect(() => {
        const fetchSession = async () => {
            const session = await getSession();
            console.log('Session data:', session);
            setSessionData(session);
            setChatHistory(session.chat_history);
            setPlan(session.current_plan);
            setStepCodes(session.step_codes);
        };

        fetchSession();
    }, []);

    const handleSSEMessage = useCallback((data: { type: string; plan?: any; step_codes?: any; chat_history?: any }) => {
        console.log('SSE Message:', data);
        if (data.type === 'plan') {
            setPlan(data.plan);
        } else if (data.type === 'code') {
            setStepCodes(data.step_codes);
        } else if (data.type === 'chat_history') {
            setChatHistory(data.chat_history);
        }
    }, []);

    if (!sessionData) {
        return <div>Loading...</div>;
    }

    return (
        <div
            style={{
                height: '100vh',
                overflow: 'hidden',
                backgroundColor: '#282a36', // 背景颜色与 Dracula 主题一致
                color: '#f8f8f2', // 文本颜色与 Dracula 主题一致
            }}
        >
            <PanelGroup direction="horizontal">
                <Panel style={{ height: '100%', overflow: 'hidden' }}>
                    <div style={{ height: '100%', overflowY: 'auto' }}>
                        <ChatWindow chatHistory={chatHistory} />
                        <SSEComponent sessionId={sessionData.session_id} onMessage={handleSSEMessage} />
                    </div>
                </Panel>
                <PanelResizeHandle style={{ backgroundColor: '#44475a', width: '5px', cursor: 'col-resize' }} />
                <Panel style={{ height: '100%', overflow: 'hidden' }}>
                    <MainWindow currentPlan={plan} stepCodes={stepCodes} />
                </Panel>
            </PanelGroup>
        </div>
    );
};

export default Home;
