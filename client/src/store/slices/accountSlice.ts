import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AccountInfo {
    account_id: string;
    pre_balance: number;
    balance: number;
    available: number;
    curr_margin: number;
    close_profit: number;
    position_profit: number;
    commission: number;
    frozen_margin: number;
    frozen_cash: number;
    frozen_commission: number;
    trading_day: string;
}

interface AccountState extends Partial<AccountInfo> {
    accountInfo: AccountInfo | null;
    loading: boolean;
    lastUpdateTime: string | null;
    // 直接暴露常用字段
    balance?: number;
    available?: number;
    margin?: number;
    unrealized_pnl?: number;
}

const initialState: AccountState = {
    accountInfo: null,
    loading: false,
    lastUpdateTime: null,
    balance: 0,
    available: 0,
    margin: 0,
    unrealized_pnl: 0,
};

const accountSlice = createSlice({
    name: 'account',
    initialState,
    reducers: {
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        updateAccountInfo: (state, action: PayloadAction<AccountInfo>) => {
            const info = action.payload;
            state.accountInfo = info;
            state.lastUpdateTime = new Date().toISOString();
            
            // 直接暴露常用字段
            state.balance = info.balance;
            state.available = info.available;
            state.margin = info.curr_margin;
            state.unrealized_pnl = info.position_profit;
        },
        clearAccountInfo: (state) => {
            state.accountInfo = null;
            state.lastUpdateTime = null;
            state.balance = 0;
            state.available = 0;
            state.margin = 0;
            state.unrealized_pnl = 0;
        },
    },
});

export const {
    setLoading,
    updateAccountInfo,
    clearAccountInfo,
} = accountSlice.actions;

export default accountSlice.reducer; 