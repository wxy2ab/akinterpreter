// 策略管理模块导出
export { default as RiskManagementPanel } from './RiskManagementPanel';
export { default as StrategyConfigEditor } from './StrategyConfigEditor';
export { default as StrategyManagementPanel } from './StrategyManagementPanel';
export { default as StrategyStatusTable } from './StrategyStatusTable';
export { default as SymbolMonitoringTable } from './SymbolMonitoringTable';

// 类型定义导出
export interface StrategyInfo {
    name: string;
    enabled: boolean;
    symbols: string[];
    alpha_threshold: number;
    position_multiplier: number | { [key: string]: number } | null;
    greed_position: boolean;
    freq: string;
    init_bars: number;
    risk_status: string;
    last_active?: string;
}

export interface MonitoredSymbol {
    symbol: string;
    product: string;
    strategy_name: string;
    added_time: string;
}

export interface RiskConfig {
    enabled: boolean;
    max_order_size: number;
    max_position_size: number;
    stop_loss_pct: number;
    daily_loss_limit: number;
}

export interface RiskStatus {
    enabled: boolean;
    daily_pnl: number;
    current_position: number;
    risk_level: string;
    last_updated: string;
}

export interface StatisticsData {
    total_strategies: number;
    enabled_strategies: number;
    disabled_strategies: number;
    total_symbols: number;
    risk_controlled_strategies: number;
    strategies_by_freq: { [key: string]: number };
    symbols_by_product: { [key: string]: number };
    last_updated: string;
}

// 常量定义
export const STRATEGY_FREQUENCIES = [
    { label: '1分钟', value: '1m' },
    { label: '5分钟', value: '5m' },
    { label: '15分钟', value: '15m' },
    { label: '30分钟', value: '30m' },
    { label: '1小时', value: '1h' },
    { label: '日线', value: '1d' }
];

export const RISK_LEVELS = {
    '正常': { color: 'green', priority: 1 },
    '注意': { color: 'blue', priority: 2 },
    '警告': { color: 'orange', priority: 3 },
    '危险': { color: 'red', priority: 4 },
    '严重': { color: 'red', priority: 5 }
};

// 工具函数
export const formatPositionMultiplier = (multiplier: number | { [key: string]: number } | null): string => {
    if (multiplier === null) {
        return '未设置';
    }

    if (typeof multiplier === 'number') {
        return multiplier.toString();
    }

    if (typeof multiplier === 'object') {
        const entries = Object.entries(multiplier);
        if (entries.length <= 2) {
            return entries.map(([symbol, value]) => `${symbol}:${value}`).join(', ');
        } else {
            return `多合约配置 (${entries.length})`;
        }
    }

    return '-';
};

export const getRiskLevelColor = (level: string): string => {
    return RISK_LEVELS[level as keyof typeof RISK_LEVELS]?.color || 'default';
};

export const calculateRiskScore = (dailyPnl: number, currentPosition: number, config: RiskConfig): number => {
    const dailyLossRatio = Math.abs(dailyPnl) / config.daily_loss_limit * 100;
    const positionRatio = Math.abs(currentPosition) / config.max_position_size * 100;
    return Math.max(dailyLossRatio, positionRatio);
};

export const isStrategyActive = (lastActive?: string, thresholdMinutes: number = 30): boolean => {
    if (!lastActive) return false;

    const lastActiveTime = new Date(lastActive);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastActiveTime.getTime()) / (1000 * 60);

    return diffMinutes < thresholdMinutes;
}; 