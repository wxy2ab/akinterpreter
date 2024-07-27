'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { getSession, updateCurrentPlan, updateStepCodes, getSSEStream, getChatList, newChat, changeChat, deleteChat } from '@/lib/api';
import '../styles/custom-tabs.css';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Sidebar, SidebarSection, SidebarItem, SidebarHeader,SidebarHeading, SidebarBody } from "@/components/sidebar"
import { Button } from "@/components/button"
import { format, isToday, isThisWeek, parseISO } from 'date-fns';

const ChatWindow = dynamic(() => import('@/components/ChatWindow'), { ssr: false });
const MainWindow = dynamic(() => import('@/components/MainWindow'), { ssr: false });

interface SessionData {
  session_id: string;
  chat_list_id: string;
  chat_history: any[];
  current_plan: any;
  step_codes: { [key: string]: string };
}

interface ChatItem {
  session_id: string;
  chat_list_id: string;
  name: string;
  date: string;
}

const sortChatsByDate = (chats: ChatItem[]): ChatItem[] => {
  return chats.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
};

const groupChatsByDate = (chats: ChatItem[]): { [key: string]: ChatItem[] } => {
  return chats.reduce((acc, chat) => {
    const date = parseISO(chat.date);
    let group = '一周外';
    if (isToday(date)) {
      group = '今天';
    } else if (isThisWeek(date, { weekStartsOn: 1 })) {
      group = '一周内';
    }
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(chat);
    return acc;
  }, {} as { [key: string]: ChatItem[] });
};


const Home: React.FC = () => {
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [chatList, setChatList] = useState<ChatItem[]>([]);
  const [leftWidth, setLeftWidth] = useState(25); // Initial width of 25%
  const [error, setError] = useState<string | null>(null);

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
      } else if (parsedData.type === 'chat_list') {
        setChatList(sortChatsByDate(parsedData.chat_list));
      }
      console.log('Updated session data:', newData);
      return newData;
    });
  }, []);

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        const [sessionData, chatListData] = await Promise.all([
          getSession(),
          getChatList()
        ]);
        console.log('Fetched session data:', sessionData);
        setSessionData(sessionData);
        
        if (Array.isArray(chatListData)) {
          setChatList(sortChatsByDate(chatListData));
        } else if (typeof chatListData === 'object' && chatListData !== null) {
          const arrayData = Object.values(chatListData).find(Array.isArray);
          if (arrayData) {
            setChatList(sortChatsByDate(arrayData));
          } else {
            throw new Error('Chat list data is not in the expected format');
          }
        } else {
          throw new Error('Unexpected data format for chat list');
        }

        const eventSource = getSSEStream(sessionData.session_id);
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
        console.error('Failed to fetch data:', error);
        setError('Failed to load initial data. Please refresh the page.');
      } finally {
        setLoading(false);
      }
    };

    fetchSessionData();
  }, [handleSSEMessage]);


  
  useEffect(() => {
    const fetchChatList = async () => {
      try {
        const list = await getChatList();
        console.log('Fetched chat list:', list);
        
        if (Array.isArray(list)) {
          setChatList(sortChatsByDate(list));
        } else if (typeof list === 'object' && list !== null) {
          const arrayData = Object.values(list).find(Array.isArray);
          if (arrayData) {
            setChatList(sortChatsByDate(arrayData));
          } else {
            throw new Error('Chat list data is not in the expected format');
          }
        } else {
          throw new Error('Unexpected data format for chat list');
        }
      } catch (error) {
        console.error('Failed to fetch chat list:', error);
        setError('Failed to load chat list. Please try again later.');
      }
    };
  
    fetchChatList();
  }, []);

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

  const handleNewPlan = async () => {
    try {
      setLoading(true);
      const newChatList = await newChat();
      console.log('New chat list:', newChatList);
      
      // 更新聊天列表
      setChatList(newChatList);
      
      // 获取新创建的聊天（列表中的第一项）
      const latestChat = newChatList[0];
      
      // 更新 sessionData
      setSessionData(prevData => ({
        ...prevData!,
        chat_list_id: latestChat.chat_list_id,
        chat_history: [],  // 清空聊天历史
        current_plan: {},  // 重置为初始值（空对象）
        step_codes: {}     // 重置为初始值（空对象）
      }));
  
      setChatList(sortChatsByDate(newChatList));
    } catch (error) {
      console.error('Failed to create new chat:', error);
      setError('Failed to create new plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleContinueChat = async (chatId: string) => {
    setLoading(true);
    setError(null); // Clear any previous errors
    try {
      const userSession = await changeChat(chatId);
      console.log('Changed to chat:', userSession);
      
      // Update sessionData with the new chat data
      setSessionData(prevData => ({
        ...prevData,
        ...userSession,
      }));
      
      // Optionally, you can add a success message here
      // setSuccessMessage('Successfully switched to the selected chat.');
    } catch (error) {
      console.error('Failed to change chat:', error);
      setError('Failed to switch to the selected chat. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteChat = async (chatId: string) => {
    try {
      setLoading(true);
      const result = await deleteChat(chatId);
      console.log('Delete chat result:', result);
      
      if (result.status) {
        // 从 chatList 中移除被删除的聊天
        setChatList(prevList => prevList.filter(chat => chat.chat_list_id !== chatId));
        
        // 如果当前会话是被删除的聊天，可能需要切换到另一个聊天或清空当前会话
        if (sessionData?.chat_list_id === chatId) {
          // 这里可以选择切换到列表中的第一个聊天，或者创建一个新的聊天
          const firstChat = chatList[0];
          if (firstChat) {
            await handleContinueChat(firstChat.chat_list_id);
          } else {
            await handleNewPlan();
          }
        }
        
        setChatList(prevList => sortChatsByDate(prevList.filter(chat => chat.chat_list_id !== chatId))); 
      } else {
        throw new Error('Failed to delete chat');
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      setError('Failed to delete the chat. Please try again.');
    } finally {
      setLoading(false);
    }
  };


  if (loading) {
    return <div className="flex justify-center items-center h-screen bg-background text-foreground">Loading...</div>;
  }
  if (error) {
    return <div className="flex justify-center items-center h-screen bg-background text-foreground">{error}</div>;
  }
  if (!sessionData) {
    return <div className="flex justify-center items-center h-screen bg-background text-foreground">No session data available.</div>;
  }


  return (
    <ResizablePanelGroup
      direction="horizontal"
      className="h-screen w-full bg-background text-foreground overflow-hidden"
    >
      <ResizablePanel defaultSize={20} minSize={15}>
        <Sidebar className="h-full">
          <SidebarHeader>
            <Button onClick={handleNewPlan} className="w-full" disabled={loading}>
              {loading ? 'Creating...' : '新计划'}
            </Button>
          </SidebarHeader>
          <SidebarBody>
            {chatList.length > 0 ? (
              Object.entries(groupChatsByDate(chatList)).map(([group, chats]) => (
                <SidebarSection key={group}>
                  <SidebarHeading>{group}</SidebarHeading>
                  {chats.map((chat) => (
                    <SidebarItem key={chat.chat_list_id}>
                      <span>{chat.name}</span>
                      <div>
                        <Button plain onClick={() => handleContinueChat(chat.chat_list_id)} disabled={loading}>
                          继续
                        </Button>
                        <Button plain onClick={() => handleDeleteChat(chat.chat_list_id)} disabled={loading}>
                          删除
                        </Button>
                      </div>
                    </SidebarItem>
                  ))}
                </SidebarSection>
              ))
            ) : (
              <div className="p-4 text-center text-gray-500">暂无聊天记录</div>
            )}
          </SidebarBody>
        </Sidebar>
      </ResizablePanel>
      <ResizableHandle />
      <ResizablePanel defaultSize={40} minSize={30}>
        <div className="h-full overflow-hidden">
          <ChatWindow 
            initialMessages={sessionData.chat_history} 
            currentPlan={sessionData.current_plan}
          />
        </div>
      </ResizablePanel>
      <ResizableHandle />
      <ResizablePanel defaultSize={40} minSize={30}>
        <div className="h-full overflow-hidden">
          <MainWindow
            currentPlan={sessionData.current_plan}
            stepCodes={sessionData.step_codes}
            onPlanUpdate={handlePlanUpdate}
            onCodeUpdate={handleCodeUpdate}
          />
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};

export default Home;