import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Position {
    symbol: string;
    direction: string;
    position: number;
    position_cost: number;
    open_cost: number;
    position_profit: number;
    close_profit: number;
    margin: number;
    exchange_margin: number;
    pre_settlement_price: number;
    settlement_price: number;
    trading_day: string;
}

export interface Order {
    order_id: string;
    symbol: string;
    direction: string;
    offset_flag: string;
    price: number;
    volume: number;
    volume_traded: number;
    volume_total: number;
    status: string;
    status_msg: string;
    insert_time: string;
    update_time: string;
    front_id: number;
    session_id: number;
}

export interface Trade {
    trade_id: string;
    order_id: string;
    symbol: string;
    direction: string;
    offset_flag: string;
    price: number;
    volume: number;
    trade_time: string;
    trade_date: string;
    commission: number;
}

interface TradingState {
    positions: Record<string, Position>;
    orders: Record<string, Order>;
    trades: Record<string, Trade>;
    loading: boolean;
    lastUpdateTime: string | null;
}

const initialState: TradingState = {
    positions: {},
    orders: {},
    trades: {},
    loading: false,
    lastUpdateTime: null,
};

const tradingSlice = createSlice({
    name: 'trading',
    initialState,
    reducers: {
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        updatePosition: (state, action: PayloadAction<Position>) => {
            const position = action.payload;
            const key = `${position.symbol}_${position.direction}`;
            state.positions[key] = position;
            state.lastUpdateTime = new Date().toISOString();
        },
        updatePositions: (state, action: PayloadAction<Record<string, Position>>) => {
            state.positions = { ...state.positions, ...action.payload };
            state.lastUpdateTime = new Date().toISOString();
        },
        updateOrder: (state, action: PayloadAction<Order>) => {
            const order = action.payload;
            state.orders[order.order_id] = order;
            state.lastUpdateTime = new Date().toISOString();
        },
        updateOrders: (state, action: PayloadAction<Record<string, Order>>) => {
            state.orders = { ...state.orders, ...action.payload };
            state.lastUpdateTime = new Date().toISOString();
        },
        updateTrade: (state, action: PayloadAction<Trade>) => {
            const trade = action.payload;
            state.trades[trade.trade_id] = trade;
            state.lastUpdateTime = new Date().toISOString();
        },
        updateTrades: (state, action: PayloadAction<Record<string, Trade>>) => {
            state.trades = { ...state.trades, ...action.payload };
            state.lastUpdateTime = new Date().toISOString();
        },
        clearTradingData: (state) => {
            state.positions = {};
            state.orders = {};
            state.trades = {};
            state.lastUpdateTime = null;
        },
    },
});

export const {
    setLoading,
    updatePosition,
    updatePositions,
    updateOrder,
    updateOrders,
    updateTrade,
    updateTrades,
    clearTradingData,
} = tradingSlice.actions;

export default tradingSlice.reducer; 