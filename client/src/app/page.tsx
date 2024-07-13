'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { getSession, updateCurrentPlan, updateStepCodes } from '@/lib/api';
import '../styles/custom-tabs.css';

const ChatWindow = dynamic(() => import('@/components/ChatWindow'), { ssr: false });
const MainWindow = dynamic(() => import('@/components/MainWindow'), { ssr: false });

interface SessionData {
  session_id: string;
  chat_history: any[];
  current_plan: any;
  step_codes: { [key: string]: string };
}

const Home: React.FC = () => {
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        const data = await getSession();
        setSessionData(data);
      } catch (error) {
        console.error('Failed to fetch session data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSessionData();
  }, []);

  const handlePlanUpdate = async (newPlan: any) => {
    if (!sessionData) return;
    try {
      await updateCurrentPlan(newPlan);
      setSessionData(prevData => ({
        ...prevData!,
        current_plan: newPlan
      }));
    } catch (error) {
      console.error('Failed to update plan:', error);
    }
  };

  const handleCodeUpdate = async (step: string, newCode: string) => {
    if (!sessionData) return;
    try {
      const updatedStepCodes = {
        ...sessionData.step_codes,
        [step]: newCode
      };
      await updateStepCodes(updatedStepCodes);
      setSessionData(prevData => ({
        ...prevData!,
        step_codes: updatedStepCodes
      }));
    } catch (error) {
      console.error('Failed to update code:', error);
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#1a202c', color: 'white' }}>Loading...</div>;
  }

  if (!sessionData) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#1a202c', color: 'white' }}>No session data available.</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#1a202c', color: 'white' }}>
      <div style={{ width: '30%', borderRight: '1px solid #4a5568' }}>
        <ChatWindow initialMessages={sessionData.chat_history} />
      </div>
      <div style={{ width: '70%' }}>
        <MainWindow
          currentPlan={sessionData.current_plan}
          stepCodes={sessionData.step_codes}
          onPlanUpdate={handlePlanUpdate}
          onCodeUpdate={handleCodeUpdate}
        />
      </div>
    </div>
  );
};

export default Home;