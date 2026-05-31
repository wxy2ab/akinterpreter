import { configureStore } from '@reduxjs/toolkit';

import accountReducer from './slices/accountSlice';
import marketReducer from './slices/marketSlice';
import strategyReducer from './slices/strategySlice';
import systemReducer from './slices/systemSlice';
import tradingReducer from './slices/tradingSlice';

export const store = configureStore({
    reducer: {
        market: marketReducer,
        trading: tradingReducer,
        account: accountReducer,
        strategy: strategyReducer,
        system: systemReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: ['persist/PERSIST'],
            },
        }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 