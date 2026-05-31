import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Strategy {
    name: string;
    enabled: boolean;
    symbols: string[];
    alpha_threshold: number;
    position_multiplier: number;
    greed_position: number;
    freq: string;
    init_bars: number;
    status?: string;
    last_signal_time?: string;
    total_signals?: number;
    performance?: any;
}

interface StrategyState {
    strategies: Record<string, Strategy>;
    loading: boolean;
    lastUpdateTime: string | null;
}

const initialState: StrategyState = {
    strategies: {},
    loading: false,
    lastUpdateTime: null,
};

const strategySlice = createSlice({
    name: 'strategy',
    initialState,
    reducers: {
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        updateStrategy: (state, action: PayloadAction<Strategy>) => {
            const strategy = action.payload;
            state.strategies[strategy.name] = strategy;
            state.lastUpdateTime = new Date().toISOString();
        },
        updateStrategies: (state, action: PayloadAction<Record<string, Strategy>>) => {
            state.strategies = { ...state.strategies, ...action.payload };
            state.lastUpdateTime = new Date().toISOString();
        },
        clearStrategies: (state) => {
            state.strategies = {};
            state.lastUpdateTime = null;
        },
    },
});

export const {
    setLoading,
    updateStrategy,
    updateStrategies,
    clearStrategies,
} = strategySlice.actions;

export default strategySlice.reducer; 