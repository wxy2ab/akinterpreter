import React, { useCallback, useMemo } from 'react';
import './PositionsTable.css';

// 类型定义
interface PositionInfo {
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

interface PositionsTableProps {
    positions: PositionInfo[];
    onRefresh: () => void;
    className?: string;
}

const PositionsTable: React.FC<PositionsTableProps> = ({
    positions,
    onRefresh,
    className
}) => {
    // 快速平仓
    const handleQuickClose = useCallback(async (position: PositionInfo) => {
        const direction = position.direction === 'LONG' ? 'long' : 'short';
        const confirmMessage = `确认平掉 ${position.symbol} 的${position.direction === 'LONG' ? '多仓' : '空仓'}？`;

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            const response = await fetch('/api/trading-management/quick-close', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: position.symbol,
                    direction: direction.toUpperCase(),
                }),
            });

            const result = await response.json();
            if (result.success) {
                alert(`平仓请求提交成功！`);
                onRefresh();
            } else {
                alert(`平仓失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('快速平仓失败:', error);
            alert('快速平仓失败，请检查网络连接');
        }
    }, [onRefresh]);

    // 计算汇总数据
    const summary = useMemo(() => {
        const totalPnl = positions.reduce((sum, pos) => {
            const positionPnl = pos.positionPnl || 0;
            const closePnl = pos.closePnl || 0;
            return sum + positionPnl + closePnl;
        }, 0);
        const totalMargin = positions.reduce((sum, pos) => sum + (pos.margin || 0), 0);
        const longPositions = positions.filter(pos => pos.direction === 'LONG');
        const shortPositions = positions.filter(pos => pos.direction === 'SHORT');

        return {
            totalPositions: positions.length,
            longCount: longPositions.length,
            shortCount: shortPositions.length,
            totalPnl,
            totalMargin
        };
    }, [positions]);

    // 格式化数字
    const formatNumber = useCallback((value: number | undefined | null, decimals: number = 2): string => {
        if (value === null || value === undefined || isNaN(value)) {
            return '--';
        }
        return value.toFixed(decimals);
    }, []);

    // 格式化百分比
    const formatPercentage = useCallback((current: number | undefined | null, avg: number | undefined | null): string => {
        if (current === null || current === undefined || avg === null || avg === undefined || isNaN(current) || isNaN(avg) || avg === 0) {
            return '--';
        }
        const percentage = ((current - avg) / avg) * 100;
        return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
    }, []);

    // 获取盈亏颜色类名
    const getPnlClassName = useCallback((value: number | undefined | null): string => {
        if (value === null || value === undefined || isNaN(value)) {
            return '';
        }
        return value >= 0 ? 'profit' : 'loss';
    }, []);

    return (
        <div className={`positions-table ${className || ''}`}>
            {/* 头部控制区 */}
            <div className="table-header">
                <div className="header-left">
                    <h3>持仓信息</h3>
                    <div className="summary-stats">
                        <span>总计: {summary.totalPositions}</span>
                        <span>多仓: {summary.longCount}</span>
                        <span>空仓: {summary.shortCount}</span>
                        <span className={`pnl ${getPnlClassName(summary.totalPnl)}`}>
                            总盈亏: {formatNumber(summary.totalPnl)}
                        </span>
                        <span>保证金: {formatNumber(summary.totalMargin)}</span>
                    </div>
                </div>

                <div className="header-right">
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
                {positions.length > 0 ? (
                    <table className="positions-table-content">
                        <thead>
                            <tr>
                                <th>合约</th>
                                <th>方向</th>
                                <th>持仓量</th>
                                <th>可用量</th>
                                <th>今仓</th>
                                <th>昨仓</th>
                                <th>开仓均价</th>
                                <th>现价</th>
                                <th>涨跌幅</th>
                                <th>盯市盈亏</th>
                                <th>浮动盈亏</th>
                                <th>保证金</th>
                                <th>更新时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions.map((position, index) => (
                                <tr key={`${position.symbol}_${position.direction}_${index}`}>
                                    <td className="symbol-cell">
                                        <span className="symbol-name">{position.symbol}</span>
                                    </td>
                                    <td className="direction-cell">
                                        <span className={`direction-badge ${position.direction.toLowerCase()}`}>
                                            {position.direction === 'LONG' ? '多' : '空'}
                                        </span>
                                    </td>
                                    <td className="volume-cell">{position.volume}</td>
                                    <td className="available-cell">{position.availableVolume}</td>
                                    <td className="today-cell">{position.todayVolume}</td>
                                    <td className="yesterday-cell">{position.yesterdayVolume}</td>
                                    <td className="price-cell">{formatNumber(position.avgPrice)}</td>
                                    <td className="price-cell">{formatNumber(position.marketPrice)}</td>
                                    <td className={`percentage-cell ${getPnlClassName(position.marketPrice - position.avgPrice)}`}>
                                        {formatPercentage(position.marketPrice, position.avgPrice)}
                                    </td>
                                    <td className={`pnl-cell ${getPnlClassName(position.positionPnl)}`}>
                                        {formatNumber(position.positionPnl)}
                                    </td>
                                    <td className={`pnl-cell ${getPnlClassName(position.closePnl)}`}>
                                        {formatNumber(position.closePnl)}
                                    </td>
                                    <td className="margin-cell">{formatNumber(position.margin)}</td>
                                    <td className="time-cell">
                                        {new Date(position.lastUpdated).toLocaleTimeString()}
                                    </td>
                                    <td className="action-cell">
                                        <button
                                            className="action-btn close-btn"
                                            onClick={() => handleQuickClose(position)}
                                            title={`平${position.direction === 'LONG' ? '多' : '空'}仓`}
                                        >
                                            平仓
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                        {/* 汇总行 */}
                        <tfoot>
                            <tr className="summary-row">
                                <td colSpan={9}>合计</td>
                                <td className={`pnl-cell ${getPnlClassName(positions.reduce((sum, pos) => sum + pos.positionPnl, 0))}`}>
                                    {formatNumber(positions.reduce((sum, pos) => sum + pos.positionPnl, 0))}
                                </td>
                                <td className={`pnl-cell ${getPnlClassName(positions.reduce((sum, pos) => sum + pos.closePnl, 0))}`}>
                                    {formatNumber(positions.reduce((sum, pos) => sum + pos.closePnl, 0))}
                                </td>
                                <td className="margin-cell">
                                    {formatNumber(positions.reduce((sum, pos) => sum + pos.margin, 0))}
                                </td>
                                <td colSpan={2}></td>
                            </tr>
                        </tfoot>
                    </table>
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">📊</div>
                        <div className="empty-text">暂无持仓</div>
                        <div className="empty-subtitle">当前账户没有持仓信息</div>
                    </div>
                )}
            </div>

            {/* 说明信息 */}
            <div className="table-footer">
                <div className="legend">
                    <span className="legend-item">
                        <span className="legend-color profit"></span>
                        盈利
                    </span>
                    <span className="legend-item">
                        <span className="legend-color loss"></span>
                        亏损
                    </span>
                    <span className="legend-item">
                        <span className="legend-color long"></span>
                        多仓
                    </span>
                    <span className="legend-item">
                        <span className="legend-color short"></span>
                        空仓
                    </span>
                </div>
                <div className="update-info">
                    数据更新时间: {new Date().toLocaleString()}
                </div>
            </div>
        </div>
    );
};

export default React.memo(PositionsTable); 