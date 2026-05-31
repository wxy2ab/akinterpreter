import { Modal, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import React, { useCallback, useMemo, useState } from 'react';
import './AlgoOrdersTable.css';

const { confirm } = Modal;

interface AlgoOrderInfo {
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

interface AlgoOrdersTableProps {
    algoOrders: AlgoOrderInfo[];
    onRefresh: () => void;
    className?: string;
}

const AlgoOrdersTable: React.FC<AlgoOrdersTableProps> = ({
    algoOrders,
    onRefresh,
    className
}) => {
    // 状态过滤
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // 控制算法订单
    const handleControlOrder = useCallback(async (order: AlgoOrderInfo, action: 'pause' | 'resume' | 'stop') => {
        const actionNames = {
            'pause': '暂停',
            'resume': '恢复',
            'stop': '停止'
        };

        confirm({
            title: `确认${actionNames[action]}算法订单？`,
            content: `订单ID: ${order.algoOrderId}`,
            onOk: async () => {
                await executeAction();
            }
        });

        const executeAction = async () => {
            setIsSubmitting(true);
            try {
                const response = await fetch(`/api/trading-management/algo-order/${order.algoOrderId}/control`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        algo_order_id: order.algoOrderId,
                        action: action
                    }),
                });

                const result = await response.json();
                if (result.success) {
                    alert(`算法订单${actionNames[action]}成功`);
                    onRefresh();
                } else {
                    alert(`算法订单${actionNames[action]}失败: ${result.detail || '未知错误'}`);
                }
            } catch (error) {
                console.error(`控制算法订单失败:`, error);
                alert(`算法订单${actionNames[action]}失败，请检查网络连接`);
            } finally {
                setIsSubmitting(false);
            }
        };
    }, [onRefresh]);

    // 根据状态过滤订单
    const filteredOrders = useMemo(() => {
        if (statusFilter === 'all') {
            return algoOrders;
        }
        return algoOrders.filter(order => order.status === statusFilter);
    }, [algoOrders, statusFilter]);

    // 订单统计
    const orderStats = useMemo(() => {
        const all = algoOrders.length;
        const running = algoOrders.filter(o => o.status === 'RUNNING').length;
        const paused = algoOrders.filter(o => o.status === 'PAUSED').length;
        const completed = algoOrders.filter(o => o.status === 'COMPLETED').length;
        const cancelled = algoOrders.filter(o => o.status === 'CANCELLED').length;
        const failed = algoOrders.filter(o => o.status === 'FAILED').length;

        return { all, running, paused, completed, cancelled, failed };
    }, [algoOrders]);

    // 格式化时间
    const formatTime = useCallback((timeStr: string): string => {
        return new Date(timeStr).toLocaleString();
    }, []);

    // 计算执行时长
    const calculateDuration = useCallback((startTime: string, endTime?: string): string => {
        const start = new Date(startTime);
        const end = endTime ? new Date(endTime) : new Date();
        const diffMs = end.getTime() - start.getTime();

        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    }, []);

    // 获取状态显示文本
    const getStatusText = useCallback((status: string): string => {
        const statusMap: Record<string, string> = {
            'PENDING': '待启动',
            'RUNNING': '运行中',
            'PAUSED': '已暂停',
            'COMPLETED': '已完成',
            'CANCELLED': '已取消',
            'FAILED': '失败'
        };
        return statusMap[status] || status;
    }, []);

    // 获取状态样式类
    const getStatusClassName = useCallback((status: string): string => {
        const classMap: Record<string, string> = {
            'PENDING': 'pending',
            'RUNNING': 'running',
            'PAUSED': 'paused',
            'COMPLETED': 'completed',
            'CANCELLED': 'cancelled',
            'FAILED': 'failed'
        };
        return classMap[status] || 'unknown';
    }, []);

    // 获取算法显示文本
    const getAlgorithmText = useCallback((algorithm: string): string => {
        const algoMap: Record<string, string> = {
            'TWAP': 'TWAP',
            'ICEBERG': '冰山',
            'SMART': '智能'
        };
        return algoMap[algorithm] || algorithm;
    }, []);

    // 获取方向显示文本
    const getDirectionText = useCallback((direction: string): string => {
        return direction === 'BUY' ? '买入' : '卖出';
    }, []);

    // 格式化算法参数
    const formatParams = useCallback((algorithm: string, params: Record<string, any>): string => {
        switch (algorithm) {
            case 'TWAP':
                return `时长:${params.duration}s, 切片:${params.slice_count}`;
            case 'ICEBERG':
                return `每笔:${params.slice_size}, 间隔:${params.interval}s`;
            case 'SMART':
                return '智能策略';
            default:
                return '-';
        }
    }, []);

    const columns: ColumnsType<AlgoOrderInfo> = [
        {
            title: '算法订单ID',
            dataIndex: 'algoOrderId',
            key: 'algoOrderId',
            width: 140,
            fixed: 'left',
            render: (algoOrderId: string) => (
                <span style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                    {algoOrderId.slice(-8)}
                </span>
            ),
        },
        {
            title: '合约',
            dataIndex: 'symbol',
            key: 'symbol',
            width: 100,
        },
        {
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            width: 60,
            render: (direction: string) => (
                <Tag color={direction === 'BUY' ? 'red' : 'green'}>
                    {getDirectionText(direction)}
                </Tag>
            ),
        },
        {
            title: '总数量',
            dataIndex: 'totalVolume',
            key: 'totalVolume',
            width: 80,
            render: (value: number) => value.toLocaleString('zh-CN', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }),
        },
        {
            title: '已成交',
            dataIndex: 'filledVolume',
            key: 'filledVolume',
            width: 80,
            render: (value: number) => value.toLocaleString('zh-CN', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }),
        },
        {
            title: '进度',
            dataIndex: 'progress',
            key: 'progress',
            width: 100,
            render: (progress: number) => (
                <div className="progress-container">
                    <div
                        className="progress-bar"
                        style={{ width: `${progress}%` }}
                    ></div>
                    <span className="progress-text">{progress.toFixed(1)}%</span>
                </div>
            ),
        },
        {
            title: '均价',
            dataIndex: 'avgPrice',
            key: 'avgPrice',
            width: 80,
            render: (value: number) => value > 0 ? value.toFixed(2) : '-',
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => (
                <Tag color={getStatusClassName(status)}>
                    {getStatusText(status)}
                </Tag>
            ),
        },
        {
            title: '算法类型',
            dataIndex: 'algorithm',
            key: 'algorithm',
            width: 100,
            render: (algorithm: string) => (
                <Tag color="purple">
                    {getAlgorithmText(algorithm)}
                </Tag>
            ),
        },
        {
            title: '开始时间',
            dataIndex: 'startTime',
            key: 'startTime',
            width: 120,
            render: (time: string) => formatTime(time),
        },
        {
            title: '执行时长',
            dataIndex: 'endTime',
            key: 'endTime',
            width: 120,
            render: (endTime: string | undefined, record: AlgoOrderInfo) => calculateDuration(record.startTime, endTime),
        },
        {
            title: '算法参数',
            dataIndex: 'params',
            key: 'params',
            width: 200,
            ellipsis: true,
            render: (params: Record<string, any>) => (
                <span style={{ fontSize: '12px', color: '#666' }}>
                    {formatParams(params.algorithm, params)}
                </span>
            ),
        },
        {
            title: '子订单',
            dataIndex: 'childOrders',
            key: 'childOrders',
            width: 80,
            render: (childOrders: string[]) => (
                <span className="child-orders-count">
                    {childOrders.length}个
                </span>
            ),
        },
        {
            title: '备注',
            dataIndex: 'notes',
            key: 'notes',
            width: 200,
            ellipsis: true,
            render: (notes?: string) => (
                <span className="notes-text" title={notes}>
                    {notes || '-'}
                </span>
            ),
        },
        {
            title: '操作',
            key: 'actions',
            width: 80,
            fixed: 'right',
            render: (_, record: AlgoOrderInfo) => (
                <div className="action-buttons">
                    {['RUNNING', 'PAUSED'].includes(record.status) && (
                        <button
                            className="action-btn stop-btn"
                            onClick={() => handleControlOrder(record, 'stop')}
                            disabled={isSubmitting}
                            title="停止执行"
                        >
                            停止
                        </button>
                    )}
                    {!['RUNNING', 'PAUSED'].includes(record.status) && (
                        <span className="no-action">-</span>
                    )}
                </div>
            ),
        },
    ];

    return (
        <div className={`algo-orders-table ${className || ''}`}>
            {/* 头部控制区 */}
            <div className="table-header">
                <div className="header-left">
                    <h3>算法订单</h3>
                    <div className="order-stats">
                        <span>全部: {orderStats.all}</span>
                        <span>运行中: {orderStats.running}</span>
                        <span>已暂停: {orderStats.paused}</span>
                        <span>已完成: {orderStats.completed}</span>
                        <span>已取消: {orderStats.cancelled}</span>
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
                            <option value="RUNNING">运行中</option>
                            <option value="PAUSED">已暂停</option>
                            <option value="COMPLETED">已完成</option>
                            <option value="CANCELLED">已取消</option>
                            <option value="FAILED">失败</option>
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
                    <table className="algo-orders-table-content">
                        <thead>
                            <tr>
                                <th>算法订单ID</th>
                                <th>合约</th>
                                <th>方向</th>
                                <th>算法</th>
                                <th>总数量</th>
                                <th>已成交</th>
                                <th>进度</th>
                                <th>均价</th>
                                <th>状态</th>
                                <th>开始时间</th>
                                <th>执行时长</th>
                                <th>算法参数</th>
                                <th>子订单</th>
                                <th>备注</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredOrders.map((order, index) => (
                                <tr key={`${order.algoOrderId}_${index}`}>
                                    <td className="order-id-cell">
                                        <span className="algo-order-id" title={order.algoOrderId}>
                                            {order.algoOrderId.slice(-8)}
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
                                    <td className="algorithm-cell">
                                        <span className="algorithm-name">{getAlgorithmText(order.algorithm)}</span>
                                    </td>
                                    <td className="volume-cell">{order.totalVolume}</td>
                                    <td className="filled-cell">{order.filledVolume}</td>
                                    <td className="progress-cell">
                                        <div className="progress-container">
                                            <div
                                                className="progress-bar"
                                                style={{ width: `${order.progress}%` }}
                                            ></div>
                                            <span className="progress-text">{order.progress.toFixed(1)}%</span>
                                        </div>
                                    </td>
                                    <td className="price-cell">
                                        {order.avgPrice > 0 ? order.avgPrice.toFixed(2) : '-'}
                                    </td>
                                    <td className="status-cell">
                                        <span className={`status-badge ${getStatusClassName(order.status)}`}>
                                            {getStatusText(order.status)}
                                        </span>
                                    </td>
                                    <td className="time-cell">
                                        {formatTime(order.startTime)}
                                    </td>
                                    <td className="duration-cell">
                                        {calculateDuration(order.startTime, order.endTime)}
                                    </td>
                                    <td className="params-cell">
                                        <span className="params-text" title={JSON.stringify(order.params)}>
                                            {formatParams(order.algorithm, order.params)}
                                        </span>
                                    </td>
                                    <td className="child-orders-cell">
                                        <span className="child-orders-count">
                                            {order.childOrders.length}个
                                        </span>
                                    </td>
                                    <td className="notes-cell">
                                        <span className="notes-text" title={order.notes}>
                                            {order.notes || '-'}
                                        </span>
                                    </td>
                                    <td className="action-cell">
                                        <div className="action-buttons">
                                            {['RUNNING', 'PAUSED'].includes(order.status) && (
                                                <button
                                                    className="action-btn stop-btn"
                                                    onClick={() => handleControlOrder(order, 'stop')}
                                                    disabled={isSubmitting}
                                                    title="停止执行"
                                                >
                                                    停止
                                                </button>
                                            )}
                                            {!['RUNNING', 'PAUSED'].includes(order.status) && (
                                                <span className="no-action">-</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="empty-state">
                        <div className="empty-icon">🤖</div>
                        <div className="empty-text">暂无算法订单</div>
                        <div className="empty-subtitle">
                            {statusFilter === 'all' ? '当前没有算法订单' : `当前没有${getStatusText(statusFilter)}的算法订单`}
                        </div>
                    </div>
                )}
            </div>

            {/* 说明信息 */}
            <div className="table-footer">
                <div className="legend">
                    <span className="legend-item">
                        <span className="legend-color running"></span>
                        运行中
                    </span>
                    <span className="legend-item">
                        <span className="legend-color paused"></span>
                        已暂停
                    </span>
                    <span className="legend-item">
                        <span className="legend-color completed"></span>
                        已完成
                    </span>
                    <span className="legend-item">
                        <span className="legend-color cancelled"></span>
                        已取消
                    </span>
                    <span className="legend-item">
                        <span className="legend-color failed"></span>
                        失败
                    </span>
                </div>
                <div className="update-info">
                    显示 {filteredOrders.length} / {algoOrders.length} 条算法订单
                </div>
            </div>
        </div>
    );
};

export default React.memo(AlgoOrdersTable); 