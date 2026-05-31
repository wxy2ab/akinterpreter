import React, { useCallback, useMemo } from 'react';
import './AccountPanel.css';

// 类型定义
interface AccountInfo {
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

interface TradingStatistics {
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

interface AccountPanelProps {
    accountInfo: AccountInfo | null;
    statistics: TradingStatistics;
    onRefresh: () => void;
    className?: string;
}

const AccountPanel: React.FC<AccountPanelProps> = ({
    accountInfo,
    statistics,
    onRefresh,
    className
}) => {
    // 计算衍生数据
    const derivedData = useMemo(() => {
        if (!accountInfo) {
            return {
                totalPnl: 0,
                usedMargin: 0,
                freeMargin: 0,
                marginRatio: 0,
                totalAssets: 0,
                netAssets: 0
            };
        }

        const totalPnl = accountInfo.closePnl + accountInfo.positionPnl;
        const usedMargin = accountInfo.margin;
        const freeMargin = accountInfo.available;
        const totalAssets = accountInfo.balance;
        const netAssets = totalAssets + totalPnl;
        const marginRatio = totalAssets > 0 ? (usedMargin / totalAssets) * 100 : 0;

        return {
            totalPnl,
            usedMargin,
            freeMargin,
            marginRatio,
            totalAssets,
            netAssets
        };
    }, [accountInfo]);

    // 格式化数字
    const formatNumber = useCallback((value: number, decimals: number = 2): string => {
        return value.toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }, []);

    // 格式化百分比
    const formatPercentage = useCallback((value: number): string => {
        return `${value.toFixed(2)}%`;
    }, []);

    // 获取盈亏颜色类名
    const getPnlClassName = useCallback((value: number): string => {
        return value >= 0 ? 'profit' : 'loss';
    }, []);

    // 获取风险等级
    const getRiskLevel = useCallback((riskRatio: number): { level: string; className: string } => {
        if (riskRatio >= 80) {
            return { level: '高风险', className: 'high-risk' };
        } else if (riskRatio >= 60) {
            return { level: '中高风险', className: 'medium-high-risk' };
        } else if (riskRatio >= 40) {
            return { level: '中等风险', className: 'medium-risk' };
        } else if (riskRatio >= 20) {
            return { level: '低风险', className: 'low-risk' };
        } else {
            return { level: '极低风险', className: 'very-low-risk' };
        }
    }, []);

    const riskInfo = accountInfo ? getRiskLevel(accountInfo.riskRatio) : { level: '未知', className: 'unknown' };

    return (
        <div className={`account-panel ${className || ''}`}>
            {/* 头部控制区 */}
            <div className="panel-header">
                <div className="header-left">
                    <h3>账户信息</h3>
                    <div className="account-id">
                        账户ID: {accountInfo?.accountId || 'N/A'}
                    </div>
                </div>

                <div className="header-right">
                    <div className="trading-day">
                        交易日: {accountInfo?.tradingDay || 'N/A'}
                    </div>
                    <button
                        className="refresh-btn"
                        onClick={onRefresh}
                    >
                        刷新
                    </button>
                </div>
            </div>

            {accountInfo ? (
                <div className="account-content">
                    {/* 资金概览 */}
                    <div className="funds-overview">
                        <h4>资金概览</h4>
                        <div className="funds-grid">
                            <div className="fund-item">
                                <span className="fund-label">账户余额</span>
                                <span className="fund-value primary">
                                    {formatNumber(accountInfo.balance)}
                                </span>
                            </div>
                            <div className="fund-item">
                                <span className="fund-label">可用资金</span>
                                <span className="fund-value">
                                    {formatNumber(accountInfo.available)}
                                </span>
                            </div>
                            <div className="fund-item">
                                <span className="fund-label">占用保证金</span>
                                <span className="fund-value">
                                    {formatNumber(accountInfo.margin)}
                                </span>
                            </div>
                            <div className="fund-item">
                                <span className="fund-label">总资产</span>
                                <span className="fund-value highlight">
                                    {formatNumber(derivedData.totalAssets)}
                                </span>
                            </div>
                            <div className="fund-item">
                                <span className="fund-label">净资产</span>
                                <span className={`fund-value ${getPnlClassName(derivedData.netAssets)}`}>
                                    {formatNumber(derivedData.netAssets)}
                                </span>
                            </div>
                            <div className="fund-item">
                                <span className="fund-label">保证金比例</span>
                                <span className={`fund-value ${riskInfo.className}`}>
                                    {formatPercentage(derivedData.marginRatio)}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 盈亏统计 */}
                    <div className="pnl-overview">
                        <h4>盈亏统计</h4>
                        <div className="pnl-grid">
                            <div className="pnl-item">
                                <span className="pnl-label">持仓盈亏</span>
                                <span className={`pnl-value ${getPnlClassName(accountInfo.positionPnl)}`}>
                                    {formatNumber(accountInfo.positionPnl)}
                                </span>
                            </div>
                            <div className="pnl-item">
                                <span className="pnl-label">平仓盈亏</span>
                                <span className={`pnl-value ${getPnlClassName(accountInfo.closePnl)}`}>
                                    {formatNumber(accountInfo.closePnl)}
                                </span>
                            </div>
                            <div className="pnl-item">
                                <span className="pnl-label">总盈亏</span>
                                <span className={`pnl-value ${getPnlClassName(derivedData.totalPnl)} highlight`}>
                                    {formatNumber(derivedData.totalPnl)}
                                </span>
                            </div>
                            <div className="pnl-item">
                                <span className="pnl-label">手续费</span>
                                <span className="pnl-value loss">
                                    {formatNumber(accountInfo.commission)}
                                </span>
                            </div>
                            <div className="pnl-item">
                                <span className="pnl-label">净盈亏</span>
                                <span className={`pnl-value ${getPnlClassName(statistics.netPnl)} highlight`}>
                                    {formatNumber(statistics.netPnl)}
                                </span>
                            </div>
                            <div className="pnl-item">
                                <span className="pnl-label">盈利率</span>
                                <span className={`pnl-value ${getPnlClassName(statistics.winRate - 50)}`}>
                                    {formatPercentage(statistics.winRate)}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 风险指标 */}
                    <div className="risk-overview">
                        <h4>风险指标</h4>
                        <div className="risk-indicators">
                            <div className="risk-item">
                                <span className="risk-label">风险度</span>
                                <div className="risk-meter">
                                    <div className={`risk-level ${riskInfo.className}`}>
                                        {riskInfo.level}
                                    </div>
                                    <div className="risk-percentage">
                                        {formatPercentage(accountInfo.riskRatio)}
                                    </div>
                                </div>
                            </div>
                            <div className="risk-item">
                                <span className="risk-label">保证金比例</span>
                                <div className="margin-ratio-bar">
                                    <div
                                        className="margin-ratio-fill"
                                        style={{ width: `${Math.min(derivedData.marginRatio, 100)}%` }}
                                    ></div>
                                    <span className="margin-ratio-text">
                                        {formatPercentage(derivedData.marginRatio)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 交易统计 */}
                    <div className="trading-stats">
                        <h4>交易统计</h4>
                        <div className="stats-grid">
                            <div className="stat-item">
                                <span className="stat-label">总订单</span>
                                <span className="stat-value">{statistics.totalOrders}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">成交订单</span>
                                <span className="stat-value">{statistics.filledOrders}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">撤销订单</span>
                                <span className="stat-value">{statistics.cancelledOrders}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">总成交量</span>
                                <span className="stat-value">{statistics.filledVolume}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">成交金额</span>
                                <span className="stat-value">{formatNumber(statistics.totalTurnover)}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">盈利因子</span>
                                <span className={`stat-value ${getPnlClassName(statistics.profitFactor - 1)}`}>
                                    {statistics.profitFactor.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 更新信息 */}
                    <div className="update-info">
                        <span>最后更新: {new Date(accountInfo.lastUpdated).toLocaleString()}</span>
                    </div>
                </div>
            ) : (
                <div className="no-account-data">
                    <div className="no-data-icon">💰</div>
                    <div className="no-data-text">暂无账户数据</div>
                    <div className="no-data-subtitle">请检查账户连接状态</div>
                </div>
            )}
        </div>
    );
};

export default React.memo(AccountPanel); 