import React, { useCallback, useMemo } from 'react';
import './TradesTable.css';

// 类型定义
interface TradeInfo {
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

interface TradesTableProps {
    trades: TradeInfo[];
    onRefresh: () => void;
    className?: string;
}

const TradesTable: React.FC<TradesTableProps> = ({
    trades,
    onRefresh,
    className
}) => {
    // 成交统计
    const tradeStats = useMemo(() => {
        const totalVolume = trades.reduce((sum, trade) => sum + trade.volume, 0);
        const totalTurnover = trades.reduce((sum, trade) => sum + trade.price * trade.volume, 0);
        const totalCommission = trades.reduce((sum, trade) => sum + trade.commission, 0);
        const buyVolume = trades.filter(t => t.direction === 'BUY').reduce((sum, t) => sum + t.volume, 0);
        const sellVolume = trades.filter(t => t.direction === 'SELL').reduce((sum, t) => sum + t.volume, 0);

        return {
            totalTrades: trades.length,
            totalVolume,
            totalTurnover,
            totalCommission,
            buyVolume,
            sellVolume
        };
    }, [trades]);

    // 今日成交
    const todayTrades = useMemo(() => {
        const today = new Date().toDateString();
        return trades.filter(trade =>
            new Date(trade.tradeTime).toDateString() === today
        );
    }, [trades]);

    // 格式化时间
    const formatTime = useCallback((timeStr: string): string => {
        return new Date(timeStr).toLocaleString();
    }, []);

    // 格式化数字
    const formatNumber = useCallback((value: number, decimals: number = 2): string => {
        return value.toFixed(decimals);
    }, []);

    // 获取方向显示文本
    const getDirectionText = useCallback((direction: string): string => {
        return direction === 'BUY' ? '买入' : '卖出';
    }, []);

    // 计算成交金额
    const calculateTurnover = useCallback((price: number, volume: number): number => {
        return price * volume;
    }, []);

    return (
        <div className={`trades-table ${className || ''}`}>
            {/* 头部控制区 */}
            <div className="table-header">
                <div className="header-left">
                    <h3>成交记录</h3>
                    <div className="trade-stats">
                        <span>总成交: {tradeStats.totalTrades}</span>
                        <span>总量: {tradeStats.totalVolume}</span>
                        <span>买入: {tradeStats.buyVolume}</span>
                        <span>卖出: {tradeStats.sellVolume}</span>
                        <span>成交额: {formatNumber(tradeStats.totalTurnover)}</span>
                        <span>手续费: {formatNumber(tradeStats.totalCommission)}</span>
                    </div>
                </div>

                <div className="header-right">
                    <div className="today-stats">
                        今日成交: {todayTrades.length} 笔
                    </div>
                    <button
                        className="refresh-btn"
                        onClick={onRefresh}
                    >
                        刷新
                    </button>
                </div>
            </div>

            {/* 表格内容 */}
            <div className="table-container">
                {trades.length > 0 ? (
                    <table className="trades-table-content">
                        <thead>
                            <tr>
                                <th>成交号</th>
                                <th>订单号</th>
                                <th>合约</th>
                                <th>方向</th>
                                <th>成交价</th>
                                <th>成交量</th>
                                <th>成交金额</th>
                                <th>手续费</th>
                                <th>成交时间</th>
                                <th>备注</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map((trade, index) => (
                                <tr key={`${trade.tradeId}_${index}`}>
                                    <td className="trade-id-cell">
                                        <span className="trade-id" title={trade.tradeId}>
                                            {trade.tradeId.slice(-8)}
                                        </span>
                                    </td>
                                    <td className="order-id-cell">
                                        <span className="order-id" title={trade.orderId}>
                                            {trade.orderId.slice(-8)}
                                        </span>
                                    </td>
                                    <td className="symbol-cell">
                                        <span className="symbol-name">{trade.symbol}</span>
                                    </td>
                                    <td className="direction-cell">
                                        <span className={`direction-badge ${trade.direction.toLowerCase()}`}>
                                            {getDirectionText(trade.direction)}
                                        </span>
                                    </td>
                                    <td className="price-cell">{formatNumber(trade.price)}</td>
                                    <td className="volume-cell">{trade.volume}</td>
                                    <td className="turnover-cell">
                                        {formatNumber(calculateTurnover(trade.price, trade.volume))}
                                    </td>
                                    <td className="commission-cell">{formatNumber(trade.commission)}</td>
                                    <td className="time-cell">
                                        {formatTime(trade.tradeTime)}
                                    </td>
                                    <td className="notes-cell">
                                        <span className="notes-text" title={trade.notes}>
                                            {trade.notes || '-'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                        {/* 汇总行 */}
                        <tfoot>
                            <tr className="summary-row">
                                <td colSpan={5}>合计</td>
                                <td className="volume-cell">{tradeStats.totalVolume}</td>
                                <td className="turnover-cell">{formatNumber(tradeStats.totalTurnover)}</td>
                                <td className="commission-cell">{formatNumber(tradeStats.totalCommission)}</td>
                                <td colSpan={2}></td>
                            </tr>
                        </tfoot>
                    </table>
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">📈</div>
                        <div className="empty-text">暂无成交记录</div>
                        <div className="empty-subtitle">当前没有成交记录</div>
                    </div>
                )}
            </div>

            {/* 说明信息 */}
            <div className="table-footer">
                <div className="legend">
                    <span className="legend-item">
                        <span className="legend-color buy"></span>
                        买入
                    </span>
                    <span className="legend-item">
                        <span className="legend-color sell"></span>
                        卖出
                    </span>
                </div>
                <div className="update-info">
                    显示最近 {trades.length} 笔成交
                </div>
            </div>
        </div>
    );
};

export default React.memo(TradesTable); 