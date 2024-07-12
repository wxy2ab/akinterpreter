// src/lib/api.ts
import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = '/api/sessions';
const SESSION_COOKIE_NAME = 'session_id';

export const setSessionCookie = (sessionId: string) => {
    Cookies.set(SESSION_COOKIE_NAME, sessionId, { expires: 7 }); // 设置cookie有效期为7天
};

export const getSessionCookie = (): string => {
    return Cookies.get(SESSION_COOKIE_NAME) || '';
};

export const createSession = async () => {
    const response = await axios.post(API_BASE_URL);
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
    const response = await axios.get(`${API_BASE_URL}/${sessionId}`);
    return response.data;
};

export const updateChatHistory = async (chatHistory: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/${sessionId}/chat_history`, chatHistory);
    return response.data;
};

export const updateCurrentPlan = async (currentPlan: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/${sessionId}/current_plan`, currentPlan);
    return response.data;
};

export const updateStepCodes = async (stepCodes: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/${sessionId}/step_codes`, stepCodes);
    return response.data;
};

export const updateData = async (data: any) => {
    const sessionId = await getSessionId();
    const response = await axios.put(`${API_BASE_URL}/${sessionId}/data`, data);
    return response.data;
};

export const fetchSessionData = async () => {
    const sessionId = await getSessionId();
    const response = await axios.get(`${API_BASE_URL}/${sessionId}/fetch_data`);
    return response.data;
};

export const deleteSession = async () => {
    const sessionId = await getSessionId();
    const response = await axios.delete(`${API_BASE_URL}/${sessionId}`);
    Cookies.remove(SESSION_COOKIE_NAME); // 删除cookie
    return response.data;
};
