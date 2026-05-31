import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { SystemStatus } from '../../types/system';

interface SystemState {
    status: SystemStatus | null;
    connected: boolean;
    loading: boolean;
    error: string | null;
    logs: string[];
    lastUpdateTime: string | null;
}

const initialState: SystemState = {
    status: null,
    connected: false,
    loading: false,
    error: null,
    logs: [],
    lastUpdateTime: null,
};

const systemSlice = createSlice({
    name: 'system',
    initialState,
    reducers: {
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        setConnected: (state, action: PayloadAction<boolean>) => {
            state.connected = action.payload;
        },
        setError: (state, action: PayloadAction<string | null>) => {
            state.error = action.payload;
        },
        updateSystemStatus: (state, action: PayloadAction<SystemStatus>) => {
            state.status = action.payload;
            state.lastUpdateTime = new Date().toISOString();
        },
        addLog: (state, action: PayloadAction<string>) => {
            state.logs.push(action.payload);
            // 保持最新的100条日志
            if (state.logs.length > 100) {
                state.logs = state.logs.slice(-100);
            }
        },
        clearLogs: (state) => {
            state.logs = [];
        },
        clearSystemData: (state) => {
            state.status = null;
            state.error = null;
            state.logs = [];
            state.lastUpdateTime = null;
        },
    },
});

export const {
    setLoading,
    setConnected,
    setError,
    updateSystemStatus,
    addLog,
    clearLogs,
    clearSystemData,
} = systemSlice.actions;

export default systemSlice.reducer; 