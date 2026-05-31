import React, { useCallback, useMemo, useState } from 'react';
import './ManualTradingPanel.css';

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

interface ManualTradingPanelProps {
    positions: PositionInfo[];
    onRefresh: () => void;
    tradingEnabled: boolean;
    className?: string;
}

interface ManualOrderData {
    symbol: string;
    direction: 'BUY' | 'SELL';
    offset: 'OPEN' | 'CLOSE' | 'CLOSE_TODAY' | 'CLOSE_YESTERDAY';
    orderType: 'LIMIT' | 'MARKET';
    price: number;
    volume: number;
    notes: string;
}

const ManualTradingPanel: React.FC<ManualTradingPanelProps> = ({
    positions,
    onRefresh,
    tradingEnabled,
    className
}) => {
    // 表单状态
    const [orderForm, setOrderForm] = useState<ManualOrderData>({
        symbol: '',
        direction: 'BUY',
        offset: 'OPEN',
        orderType: 'LIMIT',
        price: 0,
        volume: 1,
        notes: ''
    });

    // UI状态
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedSymbol, setSelectedSymbol] = useState<string>('');
    const [showQuickClose, setShowQuickClose] = useState(false);

    // 根据选中合约更新持仓信息显示
    const currentPositions = useMemo(() => {
        if (!selectedSymbol) return { long: null, short: null };

        const longPosition = positions.find(pos =>
            pos.symbol === selectedSymbol && pos.direction === 'LONG'
        );
        const shortPosition = positions.find(pos =>
            pos.symbol === selectedSymbol && pos.direction === 'SHORT'
        );

        return { long: longPosition || null, short: shortPosition || null };
    }, [selectedSymbol, positions]);

    // 处理合约代码变化
    const handleSymbolChange = useCallback((value: string) => {
        const upperSymbol = value.toUpperCase();
        setOrderForm(prev => ({ ...prev, symbol: upperSymbol }));
        setSelectedSymbol(upperSymbol);
    }, []);

    // 处理表单字段变化
    const handleFieldChange = useCallback((field: keyof ManualOrderData, value: any) => {
        setOrderForm(prev => ({ ...prev, [field]: value }));
    }, []);

    // 提交手动订单
    const handleSubmitOrder = useCallback(async () => {
        if (!tradingEnabled) {
            alert('交易功能已被禁用');
            return;
        }

        if (!orderForm.symbol) {
            alert('请输入合约代码');
            return;
        }

        if (orderForm.volume <= 0) {
            alert('请输入有效的数量');
            return;
        }

        if (orderForm.orderType === 'LIMIT' && orderForm.price <= 0) {
            alert('请输入有效的价格');
            return;
        }

        setIsSubmitting(true);
        try {
            const response = await fetch('/api/trading-management/manual-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderForm),
            });

            const result = await response.json();
            if (result.success) {
                alert(`订单提交成功！订单ID: ${result.order_id}`);
                // 重置表单（可选）
                // setOrderForm(prev => ({ ...prev, notes: '' }));
            } else {
                alert(`订单提交失败: ${result.message || '未知错误'}`);
            }
        } catch (error) {
            console.error('提交订单失败:', error);
            alert('提交订单失败，请检查网络连接');
        } finally {
            setIsSubmitting(false);
        }
    }, [orderForm, tradingEnabled]);

    // 快速平仓
    const handleQuickClose = useCallback(async (direction?: 'long' | 'short' | 'all') => {
        if (!tradingEnabled) {
            alert('交易功能已被禁用');
            return;
        }

        if (!selectedSymbol) {
            alert('请选择合约');
            return;
        }

        const confirmMessage = direction === 'all'
            ? `确认平掉 ${selectedSymbol} 的所有持仓？`
            : `确认平掉 ${selectedSymbol} 的${direction === 'long' ? '多仓' : '空仓'}？`;

        if (!confirm(confirmMessage)) {
            return;
        }

        setIsSubmitting(true);
        try {
            const response = await fetch('/api/trading-management/quick-close', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: selectedSymbol,
                    direction: direction === 'all' ? null : direction?.toUpperCase(),
                }),
            });

            const result = await response.json();
            if (result.success) {
                alert(`平仓请求提交成功！共提交 ${result.close_orders?.length || 0} 个平仓订单`);
                onRefresh(); // 刷新持仓数据
            } else {
                alert(`平仓失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('快速平仓失败:', error);
            alert('快速平仓失败，请检查网络连接');
        } finally {
            setIsSubmitting(false);
        }
    }, [selectedSymbol, tradingEnabled, onRefresh]);

    // 自动填充价格（模拟从行情获取）
    const handleFillPrice = useCallback((priceType: 'market' | 'last' | 'bid' | 'ask') => {
        // 这里可以从市场数据中获取价格
        // 暂时使用随机价格模拟
        let price = 0;
        if (currentPositions.long || currentPositions.short) {
            const basePrice = currentPositions.long?.marketPrice || currentPositions.short?.marketPrice || 3500;
            switch (priceType) {
                case 'market':
                case 'last':
                    price = basePrice;
                    break;
                case 'bid':
                    price = basePrice - 1;
                    break;
                case 'ask':
                    price = basePrice + 1;
                    break;
            }
        } else {
            price = 3500; // 默认价格
        }

        handleFieldChange('price', price);
    }, [currentPositions, handleFieldChange]);

    // 设置预设数量
    const handleSetVolume = useCallback((volume: number) => {
        handleFieldChange('volume', volume);
    }, [handleFieldChange]);

    return (
        <div className={`manual-trading-panel ${className || ''}`}>
            {/* 持仓信息显示区域 */}
            <div className="position-info-section">
                <h3>当前持仓信息</h3>

                {selectedSymbol ? (
                    <div className="position-details">
                        <div className="position-status">
                            {currentPositions.long || currentPositions.short ? (
                                <span className="has-position">{selectedSymbol} 持仓情况</span>
                            ) : (
                                <span className="no-position">{selectedSymbol} 无持仓</span>
                            )}
                        </div>

                        <div className="position-breakdown">
                            {/* 多仓信息 */}
                            <div className="position-side long-side">
                                <h4>多仓</h4>
                                <div className="position-data">
                                    <div className="data-row">
                                        <span>数量:</span>
                                        <span className="value">{currentPositions.long?.volume || 0}</span>
                                    </div>
                                    <div className="data-row">
                                        <span>均价:</span>
                                        <span className="value">{currentPositions.long?.avgPrice?.toFixed(2) || '0.00'}</span>
                                    </div>
                                    <div className="data-row">
                                        <span>盈亏:</span>
                                        <span className={`value ${(currentPositions.long?.positionPnl || 0) >= 0 ? 'profit' : 'loss'}`}>
                                            {currentPositions.long?.positionPnl?.toFixed(2) || '0.00'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* 空仓信息 */}
                            <div className="position-side short-side">
                                <h4>空仓</h4>
                                <div className="position-data">
                                    <div className="data-row">
                                        <span>数量:</span>
                                        <span className="value">{currentPositions.short?.volume || 0}</span>
                                    </div>
                                    <div className="data-row">
                                        <span>均价:</span>
                                        <span className="value">{currentPositions.short?.avgPrice?.toFixed(2) || '0.00'}</span>
                                    </div>
                                    <div className="data-row">
                                        <span>盈亏:</span>
                                        <span className={`value ${(currentPositions.short?.positionPnl || 0) >= 0 ? 'profit' : 'loss'}`}>
                                            {currentPositions.short?.positionPnl?.toFixed(2) || '0.00'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="no-symbol-selected">
                        <span>请输入合约代码</span>
                    </div>
                )}
            </div>

            {/* 交易参数输入区域 */}
            <div className="trading-params-section">
                <h3>交易参数</h3>

                <div className="form-grid">
                    {/* 合约代码 */}
                    <div className="form-group">
                        <label>合约代码:</label>
                        <input
                            type="text"
                            value={orderForm.symbol}
                            onChange={(e) => handleSymbolChange(e.target.value)}
                            placeholder="如: IF2506"
                            className="symbol-input"
                        />
                    </div>

                    {/* 方向选择 */}
                    <div className="form-group">
                        <label>买卖方向:</label>
                        <div className="direction-buttons">
                            <button
                                className={`direction-btn buy-btn ${orderForm.direction === 'BUY' ? 'active' : ''}`}
                                onClick={() => handleFieldChange('direction', 'BUY')}
                            >
                                买入开多
                            </button>
                            <button
                                className={`direction-btn sell-btn ${orderForm.direction === 'SELL' ? 'active' : ''}`}
                                onClick={() => handleFieldChange('direction', 'SELL')}
                            >
                                卖出开空
                            </button>
                        </div>
                    </div>

                    {/* 开平标志 */}
                    <div className="form-group">
                        <label>开平标志:</label>
                        <select
                            value={orderForm.offset}
                            onChange={(e) => handleFieldChange('offset', e.target.value)}
                            className="select-input"
                        >
                            <option value="OPEN">开仓</option>
                            <option value="CLOSE">平仓</option>
                            <option value="CLOSE_TODAY">平今</option>
                            <option value="CLOSE_YESTERDAY">平昨</option>
                        </select>
                    </div>

                    {/* 订单类型 */}
                    <div className="form-group">
                        <label>订单类型:</label>
                        <select
                            value={orderForm.orderType}
                            onChange={(e) => handleFieldChange('orderType', e.target.value)}
                            className="select-input"
                        >
                            <option value="LIMIT">限价</option>
                            <option value="MARKET">市价</option>
                        </select>
                    </div>

                    {/* 价格 */}
                    <div className="form-group">
                        <label>价格:</label>
                        <div className="price-input-group">
                            <input
                                type="number"
                                value={orderForm.price}
                                onChange={(e) => handleFieldChange('price', parseFloat(e.target.value) || 0)}
                                step="0.01"
                                min="0"
                                disabled={orderForm.orderType === 'MARKET'}
                                className="number-input"
                            />
                            <div className="price-buttons">
                                <button
                                    className="price-btn"
                                    onClick={() => handleFillPrice('market')}
                                    title="市场价"
                                >
                                    市价
                                </button>
                                <button
                                    className="price-btn"
                                    onClick={() => handleFillPrice('bid')}
                                    title="买一价"
                                >
                                    买一
                                </button>
                                <button
                                    className="price-btn"
                                    onClick={() => handleFillPrice('ask')}
                                    title="卖一价"
                                >
                                    卖一
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* 数量 */}
                    <div className="form-group">
                        <label>数量:</label>
                        <div className="volume-input-group">
                            <input
                                type="number"
                                value={orderForm.volume}
                                onChange={(e) => handleFieldChange('volume', parseInt(e.target.value) || 1)}
                                min="1"
                                className="number-input"
                            />
                            <div className="volume-buttons">
                                <button
                                    className="volume-btn"
                                    onClick={() => handleSetVolume(1)}
                                >
                                    1
                                </button>
                                <button
                                    className="volume-btn"
                                    onClick={() => handleSetVolume(2)}
                                >
                                    2
                                </button>
                                <button
                                    className="volume-btn"
                                    onClick={() => handleSetVolume(5)}
                                >
                                    5
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* 备注 */}
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
            </div>

            {/* 操作按钮区域 */}
            <div className="action-buttons-section">
                <h3>操作</h3>

                {/* 主操作按钮 */}
                <div className="main-actions">
                    <button
                        className="submit-btn primary"
                        onClick={handleSubmitOrder}
                        disabled={!tradingEnabled || isSubmitting}
                    >
                        {isSubmitting ? '提交中...' : '提交订单'}
                    </button>
                </div>

                {/* 快速平仓按钮 */}
                <div className="quick-close-actions">
                    <h4>快速平仓</h4>
                    <div className="close-buttons">
                        <button
                            className="close-btn long-close"
                            onClick={() => handleQuickClose('long')}
                            disabled={!tradingEnabled || !currentPositions.long || isSubmitting}
                        >
                            平多仓
                            {currentPositions.long && ` (${currentPositions.long.volume})`}
                        </button>
                        <button
                            className="close-btn short-close"
                            onClick={() => handleQuickClose('short')}
                            disabled={!tradingEnabled || !currentPositions.short || isSubmitting}
                        >
                            平空仓
                            {currentPositions.short && ` (${currentPositions.short.volume})`}
                        </button>
                        <button
                            className="close-btn all-close"
                            onClick={() => handleQuickClose('all')}
                            disabled={!tradingEnabled || (!currentPositions.long && !currentPositions.short) || isSubmitting}
                        >
                            平全部
                        </button>
                    </div>
                </div>

                {/* 交易状态提示 */}
                {!tradingEnabled && (
                    <div className="trading-disabled-notice">
                        <span>⚠️ 交易功能已被禁用</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default React.memo(ManualTradingPanel); 