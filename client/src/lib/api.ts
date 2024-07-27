import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = '/api';
const SESSION_COOKIE_NAME = 'session_id';

interface ChatItem {
    session_id: string;
    chat_list_id: string;
    name: string;
    date: string;
  }
  
// Session management functions
export const setSessionCookie = (sessionId: string) => {
    Cookies.set(SESSION_COOKIE_NAME, sessionId, { expires: 7 });
};

export const getSessionCookie = (): string => {
    return Cookies.get(SESSION_COOKIE_NAME) || '';
};

export const createSession = async () => {
    const response = await axios.post(`${API_BASE_URL}/sessions`);
    setSessionCookie(response.data.session_id);
    return response.data;
};

export const getSessionId = async (): Promise<string> => {
    let sessionId = getSessionCookie();
    if (!sessionId) {
        const response = await createSession();
        sessionId = response.session_id;
        setSessionCookie(sessionId as string);
    }
    return sessionId;
};

export const getSession = async () => {
    const sessionId = await getSessionId();
    const response = await axios.get(`${API_BASE_URL}/sessions/${sessionId}`);
    return response.data;
};

// Chat related functions
export const sendChatMessage = async (message: string): Promise<string> => {
    const sessionId = await getSessionId();
    const response = await axios.post(`${API_BASE_URL}/schat`, {
        session_id: sessionId,
        message: message
    });
    return response.data.session_id;
};

export const getChatStream = (chatSessionId: string): EventSource => {
    return new EventSource(`${API_BASE_URL}/chat-stream?session_id=${chatSessionId}`);
};

export const getSSEStream = (sessionId: string): EventSource => {
    return new EventSource(`${API_BASE_URL}/sse?session_id=${sessionId}`);
};

// Update functions
export const updateChatHistory = async (chatHistory: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/sessions/${sessionId}/chat_history`, chatHistory);
    return response.data;
};

export const updateCurrentPlan = async (sessionId: string, currentPlan: any) => {
    const response = await axios.put(
      `${API_BASE_URL}/sessions/${sessionId}/current_plan`,
      currentPlan,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  };

export const updateStepCodes = async (stepCodes: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/sessions/${sessionId}/step_codes`, stepCodes);
    return response.data;
};

export const updateData = async (data: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/sessions/${sessionId}/data`, data);
    return response.data;
};

export const fetchSessionData = async () => {
    const sessionId = await getSessionId();
    const response = await axios.get(`${API_BASE_URL}/sessions/${sessionId}/fetch_data`);
    return response.data;
};

export const deleteSession = async () => {
    const sessionId = await getSessionId();
    const response = await axios.delete(`${API_BASE_URL}/sessions/${sessionId}`);
    Cookies.remove(SESSION_COOKIE_NAME);
    return response.data;
};

// New function for saving plan
export const savePlan = async (plan: any) => {
    const sessionId = await getSessionId();
    const response = await axios.post(`${API_BASE_URL}/save_plan`, {
        session_id: sessionId,
        plan: plan
    });
    return response.data;
};

export const getChatList = async (): Promise<ChatItem[]> => {
    const sessionId = await getSessionId();
    const response = await axios.get(`${API_BASE_URL}/get_chat_list`, {
        params: { session_id: sessionId }
    });
    
    // 确保返回的数据是数组
    if (Array.isArray(response.data)) {
        return response.data;
    } else if (typeof response.data === 'object' && response.data !== null) {
        // 如果返回的是对象，尝试获取其中的数组
        const arrayData = Object.values(response.data).find(Array.isArray);
        if (arrayData) {
            return arrayData;
        }
    }
    
    // 如果无法获取到数组数据，返回空数组
    console.error('Unexpected data format from API:', response.data);
    return [];
};

export const newChat = async (): Promise<ChatItem[]> => {
    const sessionId = await getSessionId();
    try {
      const response = await axios.get(`${API_BASE_URL}/new_chat`, {
        params: { session_id: sessionId }
      });
      return response.data;
    } catch (error) {
      console.error('Error creating new chat:', error);
      throw error;
    }
  };

  export const changeChat = async (chatListId: string): Promise<any> => {
    const sessionId = await getSessionId();
    const response = await axios.get(`${API_BASE_URL}/change_chat`, {
        params: {
            session_id: sessionId,
            chat_list_id: chatListId
        }
    });
    return response.data;
};

export const deleteChat = async (chatListId: string): Promise<{ message: string; status: boolean }> => {
    const sessionId = await getSessionId();
    const response = await axios.delete(`${API_BASE_URL}/delete_chat`, {
        params: {
            session_id: sessionId,
            chat_list_id: chatListId
        }
    });
    return response.data;
};
