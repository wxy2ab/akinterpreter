import React, { useCallback, useMemo, useState } from 'react';
import './AlgoTradingPanel.css';

// 类型定义
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

interface AlgoTradingPanelProps {
    algoOrders: AlgoOrderInfo[];
    onRefresh: () => void;
    tradingEnabled: boolean;
    className?: string;
}

interface AlgoOrderForm {
    symbol: string;
    direction: 'BUY' | 'SELL';
    algorithm: 'TWAP' | 'ICEBERG' | 'SMART';
    totalVolume: number;
    params: Record<string, any>;
    notes: string;
}

const AlgoTradingPanel: React.FC<AlgoTradingPanelProps> = ({
    algoOrders,
    onRefresh,
    tradingEnabled,
    className
}) => {
    // 表单状态
    const [orderForm, setOrderForm] = useState<AlgoOrderForm>({
        symbol: '',
        direction: 'BUY',
        algorithm: 'TWAP',
        totalVolume: 10,
        params: {},
        notes: ''
    });

    // UI状态
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedOrder, setSelectedOrder] = useState<string | null>(null);

    // 处理表单字段变化
    const handleFieldChange = useCallback((field: keyof AlgoOrderForm, value: any) => {
        setOrderForm(prev => ({ ...prev, [field]: value }));
    }, []);

    // 处理算法参数变化
    const handleParamChange = useCallback((paramName: string, value: any) => {
        setOrderForm(prev => ({
            ...prev,
            params: { ...prev.params, [paramName]: value }
        }));
    }, []);

    // 提交算法订单
    const handleSubmitOrder = useCallback(async () => {
        if (!tradingEnabled) {
            alert('交易功能已被禁用');
            return;
        }

        if (!orderForm.symbol) {
            alert('请输入合约代码');
            return;
        }

        if (orderForm.totalVolume <= 0) {
            alert('请输入有效的总数量');
            return;
        }

        // 验证算法参数
        if (orderForm.algorithm === 'TWAP') {
            if (!orderForm.params.duration || !orderForm.params.slice_count) {
                alert('TWAP算法需要设置执行时长和切片数量');
                return;
            }
        } else if (orderForm.algorithm === 'ICEBERG') {
            if (!orderForm.params.slice_size || !orderForm.params.interval) {
                alert('冰山算法需要设置每笔数量和间隔时间');
                return;
            }
        }

        setIsSubmitting(true);
        try {
            const response = await fetch('/api/trading-management/algo-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderForm),
            });

            const result = await response.json();
            if (result.success) {
                alert(`算法订单提交成功！订单ID: ${result.algo_order_id}`);
                onRefresh();
                // 重置表单
                setOrderForm({
                    symbol: '',
                    direction: 'BUY',
                    algorithm: 'TWAP',
                    totalVolume: 10,
                    params: {},
                    notes: ''
                });
            } else {
                alert(`算法订单提交失败: ${result.message || '未知错误'}`);
            }
        } catch (error) {
            console.error('提交算法订单失败:', error);
            alert('提交算法订单失败，请检查网络连接');
        } finally {
            setIsSubmitting(false);
        }
    }, [orderForm, tradingEnabled, onRefresh]);

    // 控制算法订单
    const handleControlOrder = useCallback(async (orderId: string, action: 'pause' | 'resume' | 'stop') => {
        if (!tradingEnabled) {
            alert('交易功能已被禁用');
            return;
        }

        const actionNames = {
            'pause': '暂停',
            'resume': '恢复',
            'stop': '停止'
        };

        if (!confirm(`确认${actionNames[action]}算法订单 ${orderId}？`)) {
            return;
        }

        setIsSubmitting(true);
        try {
            const response = await fetch(`/api/trading-management/algo-order/${orderId}/control`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    algo_order_id: orderId,
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
    }, [tradingEnabled, onRefresh]);

    // 渲染算法参数输入
    const renderAlgoParams = useMemo(() => {
        switch (orderForm.algorithm) {
            case 'TWAP':
                return (
                    <div className="algo-params">
                        <h4>TWAP参数</h4>
                        <div className="param-group">
                            <label>执行时长(秒):</label>
                            <input
                                type="number"
                                value={orderForm.params.duration || 300}
                                onChange={(e) => handleParamChange('duration', parseInt(e.target.value) || 300)}
                                min="60"
                                max="7200"
                                className="number-input"
                            />
                        </div>
                        <div className="param-group">
                            <label>切片数量:</label>
                            <input
                                type="number"
                                value={orderForm.params.slice_count || 10}
                                onChange={(e) => handleParamChange('slice_count', parseInt(e.target.value) || 10)}
                                min="2"
                                max="100"
                                className="number-input"
                            />
                        </div>
                    </div>
                );

            case 'ICEBERG':
                return (
                    <div className="algo-params">
                        <h4>冰山算法参数</h4>
                        <div className="param-group">
                            <label>每笔数量:</label>
                            <input
                                type="number"
                                value={orderForm.params.slice_size || 5}
                                onChange={(e) => handleParamChange('slice_size', parseInt(e.target.value) || 5)}
                                min="1"
                                max="1000"
                                className="number-input"
                            />
                        </div>
                        <div className="param-group">
                            <label>间隔时间(秒):</label>
                            <input
                                type="number"
                                value={orderForm.params.interval || 30}
                                onChange={(e) => handleParamChange('interval', parseFloat(e.target.value) || 30)}
                                min="1"
                                max="300"
                                step="0.1"
                                className="number-input"
                            />
                        </div>
                    </div>
                );

            case 'SMART':
                return (
                    <div className="algo-params">
                        <h4>智能算法</h4>
                        <p className="algo-description">
                            智能算法会根据市场情况自动调整执行策略，无需额外参数设置。
                        </p>
                    </div>
                );

            default:
                return null;
        }
    }, [orderForm.algorithm, orderForm.params, handleParamChange]);

    // 活跃订单统计
    const activeOrdersStats = useMemo(() => {
        const running = algoOrders.filter(order => order.status === 'RUNNING').length;
        const paused = algoOrders.filter(order => order.status === 'PAUSED').length;
        const completed = algoOrders.filter(order => order.status === 'COMPLETED').length;
        const cancelled = algoOrders.filter(order => order.status === 'CANCELLED').length;

        return { running, paused, completed, cancelled };
    }, [algoOrders]);

    return (
        <div className={`algo-trading-panel ${className || ''}`}>
            {/* 算法订单统计 */}
            <div className="algo-stats-section">
                <h3>算法订单概览</h3>
                <div className="stats-grid">
                    <div className="stat-item running">
                        <span className="stat-label">运行中</span>
                        <span className="stat-value">{activeOrdersStats.running}</span>
                    </div>
                    <div className="stat-item paused">
                        <span className="stat-label">已暂停</span>
                        <span className="stat-value">{activeOrdersStats.paused}</span>
                    </div>
                    <div className="stat-item completed">
                        <span className="stat-label">已完成</span>
                        <span className="stat-value">{activeOrdersStats.completed}</span>
                    </div>
                    <div className="stat-item cancelled">
                        <span className="stat-label">已取消</span>
                        <span className="stat-value">{activeOrdersStats.cancelled}</span>
                    </div>
                </div>
            </div>

            {/* 新建算法订单 */}
            <div className="algo-form-section">
                <h3>新建算法订单</h3>

                <div className="form-grid">
                    {/* 基础参数 */}
                    <div className="form-group">
                        <label>合约代码:</label>
                        <input
                            type="text"
                            value={orderForm.symbol}
                            onChange={(e) => handleFieldChange('symbol', e.target.value.toUpperCase())}
                            placeholder="如: IF2506"
                            className="symbol-input"
                        />
                    </div>

                    <div className="form-group">
                        <label>买卖方向:</label>
                        <div className="direction-buttons">
                            <button
                                className={`direction-btn buy-btn ${orderForm.direction === 'BUY' ? 'active' : ''}`}
                                onClick={() => handleFieldChange('direction', 'BUY')}
                            >
                                买入
                            </button>
                            <button
                                className={`direction-btn sell-btn ${orderForm.direction === 'SELL' ? 'active' : ''}`}
                                onClick={() => handleFieldChange('direction', 'SELL')}
                            >
                                卖出
                            </button>
                        </div>
                    </div>

                    <div className="form-group">
                        <label>算法类型:</label>
                        <select
                            value={orderForm.algorithm}
                            onChange={(e) => handleFieldChange('algorithm', e.target.value)}
                            className="select-input"
                        >
                            <option value="TWAP">TWAP - 时间加权平均价格</option>
                            <option value="ICEBERG">ICEBERG - 冰山算法</option>
                            <option value="SMART">SMART - 智能算法</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>总数量:</label>
                        <input
                            type="number"
                            value={orderForm.totalVolume}
                            onChange={(e) => handleFieldChange('totalVolume', parseInt(e.target.value) || 10)}
                            min="1"
                            max="10000"
                            className="number-input"
                        />
                    </div>

                    <div className="form-group full-width">
                        <label>备注:</label>
                        <input
                            type="text"
                            value={orderForm.notes}
                            onChange={(e) => handleFieldChange('notes', e.target.value)}
                            placeholder="可选备注信息"
                            className="text-input"
                        />
                    </div>
                </div>

                {/* 算法特定参数 */}
                {renderAlgoParams}

                {/* 提交按钮 */}
                <div className="submit-section">
                    <button
                        className="submit-btn primary"
                        onClick={handleSubmitOrder}
                        disabled={!tradingEnabled || isSubmitting}
                    >
                        {isSubmitting ? '提交中...' : '提交算法订单'}
                    </button>
                </div>
            </div>

            {/* 活跃算法订单列表 */}
            <div className="active-orders-section">
                <h3>活跃算法订单</h3>

                {algoOrders.filter(order => ['RUNNING', 'PAUSED'].includes(order.status)).length > 0 ? (
                    <div className="orders-list">
                        {algoOrders
                            .filter(order => ['RUNNING', 'PAUSED'].includes(order.status))
                            .map(order => (
                                <div key={order.algoOrderId} className="order-card">
                                    <div className="order-header">
                                        <span className="order-symbol">{order.symbol}</span>
                                        <span className={`order-status ${order.status.toLowerCase()}`}>
                                            {order.status === 'RUNNING' ? '运行中' : '已暂停'}
                                        </span>
                                    </div>

                                    <div className="order-details">
                                        <div className="detail-row">
                                            <span>算法:</span>
                                            <span>{order.algorithm}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>方向:</span>
                                            <span>{order.direction === 'BUY' ? '买入' : '卖出'}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>进度:</span>
                                            <span>{order.filledVolume}/{order.totalVolume} ({order.progress.toFixed(1)}%)</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>均价:</span>
                                            <span>{order.avgPrice > 0 ? order.avgPrice.toFixed(2) : '-'}</span>
                                        </div>
                                    </div>

                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{ width: `${order.progress}%` }}
                                        ></div>
                                    </div>

                                    <div className="order-controls">
                                        {order.status === 'RUNNING' ? (
                                            <button
                                                className="control-btn pause-btn"
                                                onClick={() => handleControlOrder(order.algoOrderId, 'pause')}
                                                disabled={isSubmitting}
                                            >
                                                暂停
                                            </button>
                                        ) : (
                                            <button
                                                className="control-btn resume-btn"
                                                onClick={() => handleControlOrder(order.algoOrderId, 'resume')}
                                                disabled={isSubmitting}
                                            >
                                                恢复
                                            </button>
                                        )}
                                        <button
                                            className="control-btn stop-btn"
                                            onClick={() => handleControlOrder(order.algoOrderId, 'stop')}
                                            disabled={isSubmitting}
                                        >
                                            停止
                                        </button>
                                    </div>
                                </div>
                            ))}
                    </div>
                ) : (
                    <div className="no-active-orders">
                        <span>暂无活跃的算法订单</span>
                    </div>
                )}
            </div>

            {/* 交易状态提示 */}
            {!tradingEnabled && (
                <div className="trading-disabled-notice">
                    <span>⚠️ 交易功能已被禁用</span>
                </div>
            )}
        </div>
    );
};

export default React.memo(AlgoTradingPanel); 