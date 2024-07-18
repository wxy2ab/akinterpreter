'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { getSession, updateCurrentPlan, updateStepCodes, getSSEStream } from '@/lib/api';
import '../styles/custom-tabs.css';

const ChatWindow = dynamic(() => import('@/components/ChatWindow'), { ssr: false });
const MainWindow = dynamic(() => import('@/components/MainWindow'), { ssr: false });
const Resizer = dynamic(() => import('../components/Resizer'), { ssr: false });

interface SessionData {
  session_id: string;
  chat_history: any[];
  current_plan: any;
  step_codes: { [key: string]: string };
}

const Home: React.FC = () => {
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [leftWidth, setLeftWidth] = useState(25); // Initial width of 25%

  const validateJson = (json: any): object | any[] => {
    if (typeof json === 'object' && json !== null) {
      return json;
    }
    try {
      const parsedJson = JSON.parse(json);
      if (typeof parsedJson === 'object' && parsedJson !== null) {
        return parsedJson;
      }
    } catch (error) {
      console.error('Invalid JSON string provided, using empty object as fallback.', error);
    }
    return {};
  };

  const handleSSEMessage = useCallback((parsedData: any) => {
    console.log('Received SSE message:', parsedData);
    setSessionData((prevData) => {
      if (!prevData) return null;

      let newData = { ...prevData };
      if (parsedData.type === 'chat_history') {
        newData.chat_history = parsedData.chat_history;
      } else if (parsedData.type === 'plan') {
        newData.current_plan = validateJson(parsedData.plan);
      } else if (parsedData.type === 'code') {
        newData.step_codes = parsedData.step_codes;
      }
      console.log('Updated session data:', newData);
      return newData;
    });
  }, []);

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        const data = await getSession();
        console.log('Fetched session data:', data);
        setSessionData(data);

        const eventSource = getSSEStream(data.session_id);
        eventSource.onmessage = (event) => {
          const parsedData = JSON.parse(event.data);
          handleSSEMessage(parsedData);
        };
        eventSource.onerror = (error) => {
          console.error('EventSource failed:', error);
          eventSource.close();
        };

        return () => {
          eventSource.close();
        };
      } catch (error) {
        console.error('Failed to fetch session data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSessionData();
  }, [handleSSEMessage]);

  const handlePlanUpdate = useCallback(async (newPlan: any) => {
    if (!sessionData) return;
    console.log('Updating plan with:', newPlan);
    try {
      await updateCurrentPlan(sessionData.session_id, newPlan);
      setSessionData(prevData => {
        const updatedData = {
          ...prevData!,
          current_plan: newPlan
        };
        console.log('Updated session data after plan update:', updatedData);
        return updatedData;
      });
    } catch (error) {
      console.error('Failed to update plan:', error);
    }
  }, [sessionData]);

  const handleCodeUpdate = useCallback(async (step: string, newCode: string) => {
    if (!sessionData) return;
    console.log(`Updating code for step ${step}:`, newCode);
    try {
      const updatedStepCodes = {
        ...sessionData.step_codes,
        [step]: newCode
      };
      await updateStepCodes(updatedStepCodes);
      setSessionData(prevData => {
        const updatedData = {
          ...prevData!,
          step_codes: updatedStepCodes
        };
        console.log('Updated session data after code update:', updatedData);
        return updatedData;
      });
    } catch (error) {
      console.error('Failed to update code:', error);
    }
  }, [sessionData]);

  const handleResize = (newLeftWidth: number) => {
    setLeftWidth(newLeftWidth);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen bg-background text-foreground">Loading...</div>;
  }

  if (!sessionData) {
    return <div className="flex justify-center items-center h-screen bg-background text-foreground">No session data available.</div>;
  }

  console.log('Rendering Home component with session data:', sessionData);

  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
      <div style={{ width: `${leftWidth}%` }} className="h-full overflow-hidden">
        <ChatWindow 
          initialMessages={sessionData.chat_history} 
          currentPlan={sessionData.current_plan}
        />
      </div>
      <Resizer onResize={handleResize} />
      <div style={{ width: `${100 - leftWidth}%` }} className="h-full overflow-hidden">
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
