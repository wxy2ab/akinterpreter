import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface TickData {
    symbol: string;
    exchange?: string;
    last_price: number;
    volume: number;
    turnover: number;
    open_interest: number;
    bid_price_1: number;
    bid_volume_1: number;
    ask_price_1: number;
    ask_volume_1: number;
    highest_price?: number;
    lowest_price?: number;
    open_price?: number;
    close_price?: number;
    upper_limit_price: number;
    lower_limit_price: number;
    pre_close_price: number;
    pre_settlement_price: number;
    settlement_price?: number;
    pre_open_interest?: number;
    update_time: string;
    update_millisec?: number;
    trading_day: string;
    action_day?: string;
    change?: number;
    change_percent?: number;
}

interface MarketState {
    ticks: Record<string, TickData>;
    symbols: string[];
    loading: boolean;
    connected: boolean;
    lastUpdateTime: string | null;
    // 存储基准价格缓存，用于稳定的涨跌计算
    basePriceCache: Record<string, number>;
    // 记录价格更新次数，用于处理价格跳变
    priceUpdateCount: Record<string, number>;
}

const initialState: MarketState = {
    ticks: {},
    symbols: [],
    loading: false,
    connected: false,
    lastUpdateTime: null,
    basePriceCache: {},
    priceUpdateCount: {},
};

// 根据价格推测合约代码的辅助函数
const guessSymbolFromPrice = (price: number): string => {
    if (price >= 8000 && price <= 10000) {
        return 'rb2501'; // 螺纹钢
    } else if (price >= 3000 && price <= 5000) {
        return 'hc2501'; // 热卷
    } else if (price >= 4000 && price <= 6000) {
        return 'IM2509'; // 中证1000
    } else if (price >= 3000 && price <= 5000) {
        return 'IC2509'; // 中证500
    } else if (price >= 2000 && price <= 4000) {
        return 'IF2509'; // 沪深300
    } else if (price >= 2000 && price <= 4000) {
        return 'IH2509'; // 上证50
    }
    return `UNKNOWN_${price}`;
};

// 获取稳定的基准价格，用于计算涨跌幅
const getStableBasePrice = (
    state: MarketState,
    symbol: string,
    preSettlement: number,
    preClose: number,
    lastPrice: number
): number => {
    // 初始化计数器
    if (!state.priceUpdateCount[symbol]) {
        state.priceUpdateCount[symbol] = 0;
    }

    // 选择优先基准价格（期货优先使用昨结算价）
    const currentBase = preSettlement > 1e-6 ? preSettlement : preClose;

    // 如果当前基准价格无效，返回0
    if (currentBase <= 1e-6) {
        return 0.0;
    }

    // 首次设置基准价格
    if (!state.basePriceCache[symbol]) {
        state.basePriceCache[symbol] = currentBase;
        state.priceUpdateCount[symbol] = 1;
        console.log(`初始化基准价格 ${symbol}: ${currentBase}`);
        return currentBase;
    }

    const cachedBase = state.basePriceCache[symbol];

    // 如果基准价格没有变化，直接返回
    if (Math.abs(currentBase - cachedBase) < 1e-6) {
        return cachedBase;
    }

    // 检测价格跳变幅度
    if (cachedBase > 1e-6) {
        const changeRatio = Math.abs(currentBase - cachedBase) / cachedBase;

        // 如果跳变幅度超过5%，认为可能存在数据问题
        if (changeRatio > 0.05) {
            console.warn(`检测到基准价格跳变 ${symbol}: ${cachedBase} -> ${currentBase} (${(changeRatio * 100).toFixed(2)}%)`);

            // 检查最新价是否更接近哪个基准价格
            if (lastPrice > 1e-6) {
                const diffCached = Math.abs(lastPrice - cachedBase) / cachedBase;
                const diffCurrent = Math.abs(lastPrice - currentBase) / currentBase;

                // 如果最新价更接近缓存的基准价格，继续使用缓存
                if (diffCached < diffCurrent) {
                    console.log(`保持原基准价格 ${symbol}: ${cachedBase} (最新价更接近)`);
                    return cachedBase;
                }
            }

            // 否则需要连续确认新的基准价格
            state.priceUpdateCount[symbol] += 1;

            // 连续3次确认后才更新基准价格
            if (state.priceUpdateCount[symbol] >= 3) {
                console.log(`更新基准价格 ${symbol}: ${cachedBase} -> ${currentBase} (连续确认)`);
                state.basePriceCache[symbol] = currentBase;
                state.priceUpdateCount[symbol] = 0;
                return currentBase;
            } else {
                console.log(`等待确认基准价格 ${symbol}: ${state.priceUpdateCount[symbol]}/3`);
                return cachedBase;
            }
        } else {
            // 小幅变化，直接更新
            state.basePriceCache[symbol] = currentBase;
            state.priceUpdateCount[symbol] = 0;
            return currentBase;
        }
    }

    return currentBase;
};

// 计算涨跌和涨跌幅
const calculateChange = (lastPrice: number, basePrice: number) => {
    if (basePrice <= 1e-6) {
        return { change: 0, changePercent: 0 };
    }

    const change = lastPrice - basePrice;
    const changePercent = change / basePrice;

    return { change, changePercent };
};

const marketSlice = createSlice({
    name: 'market',
    initialState,
    reducers: {
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        setConnected: (state, action: PayloadAction<boolean>) => {
            state.connected = action.payload;
        },
        updateTick: (state, action: PayloadAction<TickData>) => {
            const tick = action.payload;

            // 处理symbol为空的情况
            let symbol = tick.symbol;
            if (!symbol || symbol.trim() === '') {
                // 根据价格推测合约代码
                symbol = guessSymbolFromPrice(tick.last_price);
                console.log(`Symbol为空，根据价格${tick.last_price}推测为: ${symbol}`);
            }

            // 获取稳定的基准价格
            const basePrice = getStableBasePrice(
                state,
                symbol,
                tick.pre_settlement_price,
                tick.pre_close_price,
                tick.last_price
            );

            // 计算涨跌和涨跌幅
            const { change, changePercent } = calculateChange(tick.last_price, basePrice);

            // 创建新的tick数据，包含计算的涨跌信息
            const updatedTick = {
                ...tick,
                symbol: symbol,
                change: change,
                change_percent: changePercent
            };

            // 如果基准价格有效，记录调试信息
            if (basePrice > 1e-6) {
                console.log(`${symbol} 价格计算: 最新价=${tick.last_price}, 基准价=${basePrice.toFixed(2)}, 涨跌=${change.toFixed(2)}, 涨跌幅=${(changePercent * 100).toFixed(2)}%`);
            } else {
                console.warn(`${symbol} 基准价格无效: 昨结算=${tick.pre_settlement_price}, 昨收盘=${tick.pre_close_price}`);
            }

            console.log('Updating tick in Redux:', symbol, updatedTick);
            state.ticks[symbol] = updatedTick;
            state.lastUpdateTime = new Date().toISOString();

            // 如果symbols数组中没有这个合约，添加进去
            if (!state.symbols.includes(symbol)) {
                state.symbols.push(symbol);
            }
        },
        updateTicks: (state, action: PayloadAction<Record<string, TickData>>) => {
            // 批量更新时也需要计算涨跌
            const updatedTicks: Record<string, TickData> = {};

            Object.entries(action.payload).forEach(([symbol, tick]) => {
                const basePrice = getStableBasePrice(
                    state,
                    symbol,
                    tick.pre_settlement_price,
                    tick.pre_close_price,
                    tick.last_price
                );

                const { change, changePercent } = calculateChange(tick.last_price, basePrice);

                updatedTicks[symbol] = {
                    ...tick,
                    change: change,
                    change_percent: changePercent
                };
            });

            state.ticks = { ...state.ticks, ...updatedTicks };
            state.lastUpdateTime = new Date().toISOString();
        },
        setSymbols: (state, action: PayloadAction<string[]>) => {
            state.symbols = action.payload;
        },
        clearMarketData: (state) => {
            state.ticks = {};
            state.basePriceCache = {};
            state.priceUpdateCount = {};
            state.lastUpdateTime = null;
        },
        // 新增：手动更新基准价格（当PriceProvider获取到正确的昨结算价时）
        updateBasePrice: (state, action: PayloadAction<{ symbol: string; basePrice: number }>) => {
            const { symbol, basePrice } = action.payload;

            if (basePrice > 1e-6) {
                const oldBasePrice = state.basePriceCache[symbol] || 0;
                state.basePriceCache[symbol] = basePrice;
                state.priceUpdateCount[symbol] = 0;

                console.log(`手动更新基准价格 ${symbol}: ${oldBasePrice} -> ${basePrice}`);

                // 重新计算该合约的涨跌
                const tick = state.ticks[symbol];
                if (tick) {
                    const { change, changePercent } = calculateChange(tick.last_price, basePrice);
                    state.ticks[symbol] = {
                        ...tick,
                        change: change,
                        change_percent: changePercent
                    };
                }
            }
        },
    },
});

export const {
    setLoading,
    setConnected,
    updateTick,
    updateTicks,
    setSymbols,
    clearMarketData,
    updateBasePrice,
} = marketSlice.actions;

export default marketSlice.reducer; 