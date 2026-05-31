import React, { useCallback, useMemo, useState } from 'react';
import './OrdersTable.css';

// 类型定义
interface OrderInfo {
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

interface OrdersTableProps {
    orders: OrderInfo[];
    onRefresh: () => void;
    className?: string;
}

const OrdersTable: React.FC<OrdersTableProps> = ({
    orders,
    onRefresh,
    className
}) => {
    // 状态过滤
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // 撤单操作
    const handleCancelOrder = useCallback(async (order: OrderInfo) => {
        if (!['SUBMITTED', 'PARTIALLY_FILLED'].includes(order.status)) {
            alert('只能撤销已提交或部分成交的订单');
            return;
        }

        if (!confirm(`确认撤销订单 ${order.orderId}？`)) {
            return;
        }

        setIsSubmitting(true);
        try {
            const response = await fetch('/api/trading-management/cancel-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order_id: order.orderId,
                    symbol: order.symbol
                }),
            });

            const result = await response.json();
            if (result.success) {
                alert('撤单请求提交成功！');
                onRefresh();
            } else {
                alert(`撤单失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('撤单失败:', error);
            alert('撤单失败，请检查网络连接');
        } finally {
            setIsSubmitting(false);
        }
    }, [onRefresh]);

    // 根据状态过滤订单
    const filteredOrders = useMemo(() => {
        if (statusFilter === 'all') {
            return orders;
        }
        return orders.filter(order => order.status === statusFilter);
    }, [orders, statusFilter]);

    // 订单统计
    const orderStats = useMemo(() => {
        const all = orders.length;
        const submitted = orders.filter(o => o.status === 'SUBMITTED').length;
        const partiallyFilled = orders.filter(o => o.status === 'PARTIALLY_FILLED').length;
        const filled = orders.filter(o => o.status === 'FILLED').length;
        const cancelled = orders.filter(o => o.status === 'CANCELLED').length;
        const rejected = orders.filter(o => o.status === 'REJECTED').length;

        return { all, submitted, partiallyFilled, filled, cancelled, rejected };
    }, [orders]);

    // 格式化时间
    const formatTime = useCallback((timeStr: string): string => {
        return new Date(timeStr).toLocaleString();
    }, []);

    // 获取状态显示文本
    const getStatusText = useCallback((status: string): string => {
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
    }, []);

    // 获取状态样式类
    const getStatusClassName = useCallback((status: string): string => {
        const classMap: Record<string, string> = {
            'PENDING': 'pending',
            'SUBMITTED': 'submitted',
            'PARTIALLY_FILLED': 'partially-filled',
            'FILLED': 'filled',
            'CANCELLED': 'cancelled',
            'REJECTED': 'rejected',
            'FAILED': 'failed'
        };
        return classMap[status] || 'unknown';
    }, []);

    // 获取方向显示文本
    const getDirectionText = useCallback((direction: string): string => {
        return direction === 'BUY' ? '买' : '卖';
    }, []);

    // 获取开平显示文本
    const getOffsetText = useCallback((offset: string): string => {
        const offsetMap: Record<string, string> = {
            'OPEN': '开仓',
            'CLOSE': '平仓',
            'CLOSE_TODAY': '平今',
            'CLOSE_YESTERDAY': '平昨'
        };
        return offsetMap[offset] || offset;
    }, []);

    return (
        <div className={`orders-table ${className || ''}`}>
            {/* 头部控制区 */}
            <div className="table-header">
                <div className="header-left">
                    <h3>委托订单</h3>
                    <div className="order-stats">
                        <span>全部: {orderStats.all}</span>
                        <span>已提交: {orderStats.submitted}</span>
                        <span>部分成交: {orderStats.partiallyFilled}</span>
                        <span>已成交: {orderStats.filled}</span>
                        <span>已撤销: {orderStats.cancelled}</span>
                    </div>
                </div>

                <div className="header-right">
                    <div className="filter-controls">
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="status-filter"
                        >
                            <option value="all">全部状态</option>
                            <option value="SUBMITTED">已提交</option>
                            <option value="PARTIALLY_FILLED">部分成交</option>
                            <option value="FILLED">全部成交</option>
                            <option value="CANCELLED">已撤销</option>
                            <option value="REJECTED">已拒绝</option>
                        </select>
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
                {filteredOrders.length > 0 ? (
                    <table className="orders-table-content">
                        <thead>
                            <tr>
                                <th>订单号</th>
                                <th>合约</th>
                                <th>方向</th>
                                <th>开平</th>
                                <th>类型</th>
                                <th>价格</th>
                                <th>数量</th>
                                <th>已成交</th>
                                <th>成交比例</th>
                                <th>状态</th>
                                <th>提交时间</th>
                                <th>更新时间</th>
                                <th>备注</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredOrders.map((order, index) => (
                                <tr key={`${order.orderId}_${index}`}>
                                    <td className="order-id-cell">
                                        <span className="order-id" title={order.orderId}>
                                            {order.orderId.slice(-8)}
                                        </span>
                                    </td>
                                    <td className="symbol-cell">
                                        <span className="symbol-name">{order.symbol}</span>
                                    </td>
                                    <td className="direction-cell">
                                        <span className={`direction-badge ${order.direction.toLowerCase()}`}>
                                            {getDirectionText(order.direction)}
                                        </span>
                                    </td>
                                    <td className="offset-cell">
                                        <span className="offset-text">{getOffsetText(order.offset)}</span>
                                    </td>
                                    <td className="type-cell">
                                        <span className="type-text">{order.orderType === 'LIMIT' ? '限价' : '市价'}</span>
                                    </td>
                                    <td className="price-cell">
                                        {order.orderType === 'MARKET' ? '市价' : order.price.toFixed(2)}
                                    </td>
                                    <td className="volume-cell">{order.volume}</td>
                                    <td className="filled-cell">{order.filledVolume}</td>
                                    <td className="progress-cell">
                                        <div className="progress-container">
                                            <div
                                                className="progress-bar"
                                                style={{
                                                    width: `${(order.filledVolume / order.volume) * 100}%`
                                                }}
                                            ></div>
                                            <span className="progress-text">
                                                {((order.filledVolume / order.volume) * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td className="status-cell">
                                        <span className={`status-badge ${getStatusClassName(order.status)}`}>
                                            {getStatusText(order.status)}
                                        </span>
                                    </td>
                                    <td className="time-cell">
                                        {formatTime(order.submitTime)}
                                    </td>
                                    <td className="time-cell">
                                        {formatTime(order.updateTime)}
                                    </td>
                                    <td className="notes-cell">
                                        <span className="notes-text" title={order.notes}>
                                            {order.notes || '-'}
                                        </span>
                                    </td>
                                    <td className="action-cell">
                                        {['SUBMITTED', 'PARTIALLY_FILLED'].includes(order.status) ? (
                                            <button
                                                className="action-btn cancel-btn"
                                                onClick={() => handleCancelOrder(order)}
                                                disabled={isSubmitting}
                                            >
                                                撤单
                                            </button>
                                        ) : (
                                            <span className="no-action">-</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">📋</div>
                        <div className="empty-text">暂无订单</div>
                        <div className="empty-subtitle">
                            {statusFilter === 'all' ? '当前没有委托订单' : `当前没有${getStatusText(statusFilter)}的订单`}
                        </div>
                    </div>
                )}
            </div>

            {/* 说明信息 */}
            <div className="table-footer">
                <div className="legend">
                    <span className="legend-item">
                        <span className="legend-color submitted"></span>
                        已提交
                    </span>
                    <span className="legend-item">
                        <span className="legend-color partially-filled"></span>
                        部分成交
                    </span>
                    <span className="legend-item">
                        <span className="legend-color filled"></span>
                        全部成交
                    </span>
                    <span className="legend-item">
                        <span className="legend-color cancelled"></span>
                        已撤销
                    </span>
                    <span className="legend-item">
                        <span className="legend-color rejected"></span>
                        已拒绝
                    </span>
                </div>
                <div className="update-info">
                    显示 {filteredOrders.length} / {orders.length} 条订单
                </div>
            </div>
        </div>
    );
};

export default React.memo(OrdersTable); 