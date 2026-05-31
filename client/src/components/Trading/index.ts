// 交易组件导出文件

// 主要组件
export { default as AccountPanel } from './AccountPanel';
export { default as AlgoTradingPanel } from './AlgoTradingPanel';
export { default as ManualTradingPanel } from './ManualTradingPanel';
export { default as TradingPanel } from './TradingPanel';
export { default as TradingStatisticsPanel } from './TradingStatisticsPanel';

// 表格组件
export { default as AlgoOrdersTable } from './AlgoOrdersTable';
export { default as OrdersTable } from './OrdersTable';
export { default as PositionsTable } from './PositionsTable';
export { default as TradesTable } from './TradesTable';

// 类型定义导出
export interface TradingStatistics {
    totalOrders: number;
    filledOrders: number;
    cancelledOrders: number;
    totalVolume: number;
    filledVolume: number;
    totalTurnover: number;
    commissionPaid: number;
    netPnl: number;
    winRate: number;
    profitFactor: number;
}

export interface PositionInfo {
    symbol: string;
    direction: string;
    volume: number;
    availableVolume: number;
    avgPrice: number;
    marketPrice: number;
    positionPnl: number;
    closePnl: number;
    margin: number;
    todayVolume: number;
    yesterdayVolume: number;
    lastUpdated: string;
}

export interface OrderInfo {
    orderId: string;
    symbol: string;
    direction: string;
    offset: string;
    orderType: string;
    price: number;
    volume: number;
    filledVolume: number;
    status: string;
    submitTime: string;
    updateTime: string;
    notes?: string;
}

export interface AlgoOrderInfo {
    algoOrderId: string;
    symbol: string;
    direction: string;
    algorithm: string;
    totalVolume: number;
    filledVolume: number;
    remainingVolume: number;
    status: string;
    progress: number;
    avgPrice: number;
    startTime: string;
    endTime?: string;
    params: Record<string, any>;
    childOrders: string[];
    notes?: string;
}

export interface TradeInfo {
    tradeId: string;
    orderId: string;
    symbol: string;
    direction: string;
    price: number;
    volume: number;
    tradeTime: string;
    commission: number;
    notes?: string;
}

export interface AccountInfo {
    accountId: string;
    balance: number;
    available: number;
    margin: number;
    closePnl: number;
    positionPnl: number;
    commission: number;
    riskRatio: number;
    tradingDay: string;
    lastUpdated: string;
}

// 常量定义
export const ORDER_DIRECTIONS = {
    BUY: 'BUY',
    SELL: 'SELL'
} as const;

export const ORDER_OFFSETS = {
    OPEN: 'OPEN',
    CLOSE: 'CLOSE',
    CLOSE_TODAY: 'CLOSE_TODAY',
    CLOSE_YESTERDAY: 'CLOSE_YESTERDAY'
} as const;

export const ORDER_TYPES = {
    LIMIT: 'LIMIT',
    MARKET: 'MARKET'
} as const;

export const ORDER_STATUSES = {
    PENDING: 'PENDING',
    SUBMITTED: 'SUBMITTED',
    PARTIALLY_FILLED: 'PARTIALLY_FILLED',
    FILLED: 'FILLED',
    CANCELLED: 'CANCELLED',
    REJECTED: 'REJECTED',
    FAILED: 'FAILED'
} as const;

export const ALGORITHM_TYPES = {
    TWAP: 'TWAP',
    ICEBERG: 'ICEBERG',
    SMART: 'SMART'
} as const;

export const ALGO_ORDER_STATUSES = {
    PENDING: 'PENDING',
    RUNNING: 'RUNNING',
    PAUSED: 'PAUSED',
    COMPLETED: 'COMPLETED',
    CANCELLED: 'CANCELLED',
    FAILED: 'FAILED'
} as const;

// 工具函数
export const formatNumber = (value: number, decimals: number = 2): string => {
    return value.toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
};

export const formatPercentage = (value: number): string => {
    return `${value.toFixed(2)}%`;
};

export const formatTime = (timeStr: string): string => {
    return new Date(timeStr).toLocaleString();
};

export const getPnlClassName = (value: number): string => {
    return value >= 0 ? 'profit' : 'loss';
};

export const getDirectionText = (direction: string): string => {
    return direction === 'BUY' ? '买入' : '卖出';
};

export const getOffsetText = (offset: string): string => {
    const offsetMap: Record<string, string> = {
        'OPEN': '开仓',
        'CLOSE': '平仓',
        'CLOSE_TODAY': '平今',
        'CLOSE_YESTERDAY': '平昨'
    };
    return offsetMap[offset] || offset;
};

export const getOrderStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
        'PENDING': '待提交',
        'SUBMITTED': '已提交',
        'PARTIALLY_FILLED': '部分成交',
        'FILLED': '全部成交',
        'CANCELLED': '已撤销',
        'REJECTED': '已拒绝',
        'FAILED': '失败'
    };
    return statusMap[status] || status;
};

export const getAlgoOrderStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
        'PENDING': '待启动',
        'RUNNING': '运行中',
        'PAUSED': '已暂停',
        'COMPLETED': '已完成',
        'CANCELLED': '已取消',
        'FAILED': '失败'
    };
    return statusMap[status] || status;
};

export const getAlgorithmText = (algorithm: string): string => {
    const algoMap: Record<string, string> = {
        'TWAP': 'TWAP',
        'ICEBERG': '冰山',
        'SMART': '智能'
    };
    return algoMap[algorithm] || algorithm;
}; 