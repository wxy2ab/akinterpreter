import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './TradingPanel.css';

// CSS样式定义
const styles = `
.status-panel {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
}

.status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.status-header h3 {
    margin: 0;
    font-size: 16px;
    color: #333;
}

.status-indicator {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.status-indicator.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status-indicator.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.status-details {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}

.status-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}

.status-item span:first-child {
    font-weight: 500;
    color: #666;
}

.status-item span.success {
    color: #28a745;
    font-weight: 500;
}

.status-item span.error {
    color: #dc3545;
    font-weight: 500;
}

.data-availability {
    margin-top: 16px;
}

.data-availability h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #333;
}

.suggestions {
    margin-top: 16px;
    padding: 12px;
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 4px;
}

.suggestions h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #856404;
}

.suggestions ul {
    margin: 0;
    padding-left: 20px;
}

.suggestions li {
    color: #856404;
    margin-bottom: 4px;
}

.debug-panel {
    background: #f1f3f4;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
}

.debug-panel h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    color: #333;
}

.debug-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
}

.debug-section {
    background: white;
    padding: 12px;
    border-radius: 4px;
    border: 1px solid #e0e0e0;
}

.debug-section h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #333;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
}

.debug-section p {
    margin: 4px 0;
    font-size: 12px;
    color: #666;
}

.debug-section pre {
    background: #f8f9fa;
    padding: 8px;
    border-radius: 4px;
    font-size: 10px;
    overflow: auto;
    max-height: 200px;
}

.btn.btn-debug {
    background-color: #6f42c1;
    color: white;
    border: 1px solid #6f42c1;
}

.btn.btn-debug:hover {
    background-color: #5a32a3;
    border-color: #5a32a3;
}

.error-message {
    color: #dc3545;
    background: #f8d7da;
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid #f5c6cb;
}
`;

// 注入样式
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('style');
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
}

// 子组件导入
import AccountPanel from './AccountPanel';
import AlgoOrdersTable from './AlgoOrdersTable';
import AlgoTradingPanel from './AlgoTradingPanel';
import ManualTradingPanel from './ManualTradingPanel';
import OrdersTable from './OrdersTable';
import PositionsTable from './PositionsTable';
import TradesTable from './TradesTable';

// WebSocket钩子
import { useWebSocket } from '../../hooks/useWebSocket';

// 类型定义
interface TradingPanelProps {
    className?: string;
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

const TradingPanel: React.FC<TradingPanelProps> = ({ className }) => {
    // 状态管理
    const [activeTab, setActiveTab] = useState<'manual' | 'algo'>('manual');
    const [infoTab, setInfoTab] = useState<'account' | 'positions' | 'orders' | 'algo-orders' | 'trades' | 'statistics'>('positions');
    const [isLoading, setIsLoading] = useState(false);
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

    // 数据状态
    const [statistics, setStatistics] = useState<TradingStatistics>({
        totalOrders: 0,
        filledOrders: 0,
        cancelledOrders: 0,
        totalVolume: 0,
        filledVolume: 0,
        totalTurnover: 0,
        commissionPaid: 0,
        netPnl: 0,
        winRate: 0,
        profitFactor: 0
    });

    const [positions, setPositions] = useState<PositionInfo[]>([]);
    const [orders, setOrders] = useState<OrderInfo[]>([]);
    const [algoOrders, setAlgoOrders] = useState<AlgoOrderInfo[]>([]);
    const [trades, setTrades] = useState<TradeInfo[]>([]);
    const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
    const [tradingEnabled, setTradingEnabled] = useState(true);
    const [riskControlEnabled, setRiskControlEnabled] = useState(true);

    // 添加CTP状态检查
    const [ctpStatus, setCtpStatus] = useState<any>(null);
    const [showDebugInfo, setShowDebugInfo] = useState(false);

    // WebSocket连接
    const { isConnected, sendMessage, lastMessage } = useWebSocket();

    // 初始化数据加载
    useEffect(() => {
        loadInitialData();
    }, []);

    // WebSocket消息处理
    useEffect(() => {
        if (lastMessage) {
            handleWebSocketMessage(lastMessage);
        }
    }, [lastMessage]);

    // 订阅WebSocket事件
    useEffect(() => {
        if (isConnected) {
            // 订阅交易相关事件
            sendMessage({
                type: 'subscribe',
                event_types: [
                    'trading_position_update',
                    'trading_order_update',
                    'trading_trade_update',
                    'trading_account_update',
                    'trading_algo_order_update',
                    'trading_risk_update'
                ]
            });
        }
    }, [isConnected, sendMessage]);

    // 加载初始数据
    const loadInitialData = useCallback(async () => {
        setIsLoading(true);
        try {
            await Promise.all([
                loadPositions(),
                loadOrders(),
                loadAlgoOrders(),
                loadTrades(),
                loadAccountInfo(),
                loadStatistics(),
                loadTradingStatus()
            ]);
            setLastRefresh(new Date());
        } catch (error) {
            console.error('加载初始数据失败:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // 加载持仓数据
    const loadPositions = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/positions');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回数组，不需要检查success字段
            setPositions(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载持仓数据失败:', error);
            setPositions([]); // 清空数据，显示真实错误状态
        }
    }, []);

    // 加载订单数据
    const loadOrders = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/orders?limit=50');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回数组，不需要检查success字段
            setOrders(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载订单数据失败:', error);
            setOrders([]); // 清空数据，显示真实错误状态
        }
    }, []);

    // 加载算法订单数据
    const loadAlgoOrders = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/algo-orders?limit=30');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回数组，不需要检查success字段
            setAlgoOrders(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载算法订单数据失败:', error);
            setAlgoOrders([]); // 清空数据，显示真实错误状态
        }
    }, []);

    // 加载成交数据
    const loadTrades = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/trades?limit=50');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回数组，不需要检查success字段
            setTrades(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载成交数据失败:', error);
            setTrades([]); // 清空数据，显示真实错误状态
        }
    }, []);

    // 加载账户信息
    const loadAccountInfo = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/account');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回对象，不需要检查success字段
            setAccountInfo(data && typeof data === 'object' ? data : null);
        } catch (error) {
            console.error('加载账户信息失败:', error);
            setAccountInfo(null); // 清空数据，显示真实错误状态
        }
    }, []);

    // 加载统计数据
    const loadStatistics = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/statistics');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回对象，不需要检查success字段
            setStatistics(data && typeof data === 'object' ? data : {
                totalOrders: 0,
                filledOrders: 0,
                cancelledOrders: 0,
                totalVolume: 0,
                filledVolume: 0,
                totalTurnover: 0,
                commissionPaid: 0,
                netPnl: 0,
                winRate: 0,
                profitFactor: 0
            });
        } catch (error) {
            console.error('加载统计数据失败:', error);
            setStatistics({
                totalOrders: 0,
                filledOrders: 0,
                cancelledOrders: 0,
                totalVolume: 0,
                filledVolume: 0,
                totalTurnover: 0,
                commissionPaid: 0,
                netPnl: 0,
                winRate: 0,
                profitFactor: 0
            }); // 使用默认值而不是null
        }
    }, []);

    // 加载交易状态
    const loadTradingStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            // API现在直接返回对象，不需要检查success字段
            if (data && typeof data === 'object') {
                setTradingEnabled(data.trading_enabled || false);
                setRiskControlEnabled(data.risk_control_enabled || false);
            }
        } catch (error) {
            console.error('加载交易状态失败:', error);
            setTradingEnabled(false);
            setRiskControlEnabled(false);
        }
    }, []);

    // 处理WebSocket消息
    const handleWebSocketMessage = useCallback((message: any) => {
        try {
            const { type, data } = message;

            switch (type) {
                case 'trading_position_update':
                    handlePositionUpdate(data);
                    break;
                case 'trading_order_update':
                    handleOrderUpdate(data);
                    break;
                case 'trading_trade_update':
                    handleTradeUpdate(data);
                    break;
                case 'trading_account_update':
                    handleAccountUpdate(data);
                    break;
                case 'trading_algo_order_update':
                    handleAlgoOrderUpdate(data);
                    break;
                case 'trading_risk_update':
                    handleRiskUpdate(data);
                    break;
                default:
                    break;
            }
        } catch (error) {
            console.error('处理WebSocket消息失败:', error);
        }
    }, []);

    // 处理持仓更新
    const handlePositionUpdate = useCallback((data: any) => {
        // 实时更新持仓数据
        loadPositions();
    }, [loadPositions]);

    // 处理订单更新
    const handleOrderUpdate = useCallback((data: any) => {
        // 实时更新订单数据
        loadOrders();
        loadStatistics();
    }, [loadOrders, loadStatistics]);

    // 处理成交更新
    const handleTradeUpdate = useCallback((data: any) => {
        // 实时更新成交数据
        loadTrades();
        loadStatistics();
    }, [loadTrades, loadStatistics]);

    // 处理账户更新
    const handleAccountUpdate = useCallback((data: any) => {
        // 实时更新账户数据
        loadAccountInfo();
    }, [loadAccountInfo]);

    // 处理算法订单更新
    const handleAlgoOrderUpdate = useCallback((data: any) => {
        // 实时更新算法订单数据
        loadAlgoOrders();
    }, [loadAlgoOrders]);

    // 处理风控更新
    const handleRiskUpdate = useCallback((data: any) => {
        // 可以在这里显示风控告警
        console.log('风控状态更新:', data);
    }, []);

    // 刷新数据
    const handleRefresh = useCallback(() => {
        loadInitialData();
    }, [loadInitialData]);

    // 初始化测试数据
    const handleInitTestData = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await fetch('/api/trading-management/test-data/initialize', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                await loadInitialData();
                alert('测试数据初始化成功');
            } else {
                alert('测试数据初始化失败');
            }
        } catch (error) {
            console.error('初始化测试数据失败:', error);
            alert('初始化测试数据失败');
        } finally {
            setIsLoading(false);
        }
    }, [loadInitialData]);

    // 清除测试数据
    const handleClearTestData = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await fetch('/api/trading-management/test-data/clear', {
                method: 'DELETE'
            });
            const data = await response.json();
            if (data.success) {
                await loadInitialData();
                alert('测试数据清除成功');
            } else {
                alert('测试数据清除失败');
            }
        } catch (error) {
            console.error('清除测试数据失败:', error);
            alert('清除测试数据失败');
        } finally {
            setIsLoading(false);
        }
    }, [loadInitialData]);

    // 强制同步CTP数据
    const forceSyncData = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await fetch('/api/trading-management/force-sync', {
                method: 'POST'
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const result = await response.json();
            console.log('强制同步结果:', result);

            // 等待一秒后重新加载数据
            setTimeout(() => {
                loadInitialData();
            }, 1000);

            alert('数据同步完成');
        } catch (error) {
            console.error('强制同步失败:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            alert('强制同步失败: ' + errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, [loadInitialData]);

    // 检查CTP状态
    const checkCtpStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/ctp-status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const status = await response.json();
            setCtpStatus(status);
            console.log('CTP状态:', status);
        } catch (error) {
            console.error('检查CTP状态失败:', error);
            const errorMessage = error instanceof Error ? error.message : String(error);
            setCtpStatus({ error: errorMessage });
        }
    }, []);

    // 组件挂载时检查CTP状态
    useEffect(() => {
        checkCtpStatus();
    }, [checkCtpStatus]);

    // 计算统计摘要
    const statisticsSummary = useMemo(() => {
        const totalPositions = positions.length;
        const totalPnl = positions.reduce((sum, pos) => sum + pos.positionPnl + pos.closePnl, 0);
        const totalMargin = positions.reduce((sum, pos) => sum + pos.margin, 0);
        const activeOrders = orders.filter(order =>
            ['SUBMITTED', 'PARTIALLY_FILLED'].includes(order.status)
        ).length;
        const runningAlgoOrders = algoOrders.filter(order =>
            ['RUNNING', 'PAUSED'].includes(order.status)
        ).length;

        return {
            totalPositions,
            totalPnl,
            totalMargin,
            activeOrders,
            runningAlgoOrders,
            todayTrades: trades.filter(trade =>
                new Date(trade.tradeTime).toDateString() === new Date().toDateString()
            ).length
        };
    }, [positions, orders, algoOrders, trades]);

    return (
        <div className={`trading-panel ${className || ''}`}>
            {/* 头部控制区 */}
            <div className="trading-panel-header">
                <div className="header-left">
                    <h2>交易面板</h2>
                    <div className="connection-status">
                        <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
                        {isConnected ? '已连接' : '未连接'}
                    </div>
                </div>

                <div className="header-right">
                    <div className="trading-status">
                        <span className={`status-badge ${tradingEnabled ? 'enabled' : 'disabled'}`}>
                            交易{tradingEnabled ? '已启用' : '已禁用'}
                        </span>
                        <span className={`status-badge ${riskControlEnabled ? 'enabled' : 'disabled'}`}>
                            风控{riskControlEnabled ? '已启用' : '已禁用'}
                        </span>
                    </div>

                    <div className="header-controls">
                        <button
                            className="btn btn-secondary"
                            onClick={handleRefresh}
                            disabled={isLoading}
                        >
                            刷新
                        </button>
                        <button
                            className="btn btn-info"
                            onClick={handleInitTestData}
                            disabled={isLoading}
                        >
                            初始化测试数据
                        </button>
                        <button
                            className="btn btn-warning"
                            onClick={handleClearTestData}
                            disabled={isLoading}
                        >
                            清除测试数据
                        </button>
                        <button
                            className="btn btn-debug"
                            onClick={forceSyncData}
                            disabled={isLoading}
                        >
                            强制同步CTP数据
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={checkCtpStatus}
                        >
                            检查CTP状态
                        </button>
                        <button
                            className="btn btn-info"
                            onClick={() => setShowDebugInfo(!showDebugInfo)}
                        >
                            {showDebugInfo ? '隐藏' : '显示'}调试信息
                        </button>
                    </div>
                </div>
            </div>

            {/* CTP状态显示 */}
            {ctpStatus && (
                <div className="status-panel">
                    <div className="status-header">
                        <h3>CTP服务状态</h3>
                        <div className={`status-indicator ${ctpStatus.ctp_manager_found && ctpStatus.ctp_manager_running ? 'success' : 'error'}`}>
                            {ctpStatus.ctp_manager_found && ctpStatus.ctp_manager_running ? '✅ 正常' : '❌ 异常'}
                        </div>
                    </div>

                    {ctpStatus.error ? (
                        <div className="error-message">错误: {ctpStatus.error}</div>
                    ) : (
                        <div className="status-details">
                            <div className="status-item">
                                <span>CTP管理器:</span>
                                <span className={ctpStatus.ctp_manager_found ? 'success' : 'error'}>
                                    {ctpStatus.ctp_manager_found ? '已找到' : '未找到'}
                                </span>
                            </div>
                            <div className="status-item">
                                <span>运行状态:</span>
                                <span className={ctpStatus.ctp_manager_running ? 'success' : 'error'}>
                                    {ctpStatus.ctp_manager_running ? '运行中' : '未运行'}
                                </span>
                            </div>

                            {/* 数据可用性状态 */}
                            {ctpStatus.data_availability && (
                                <div className="data-availability">
                                    <h4>数据可用性</h4>
                                    <div className="status-item">
                                        <span>持仓数据:</span>
                                        <span className={ctpStatus.data_availability.positions?.success ? 'success' : 'error'}>
                                            {ctpStatus.data_availability.positions?.success
                                                ? `✅ ${ctpStatus.data_availability.positions.count}个持仓`
                                                : `❌ ${ctpStatus.data_availability.positions?.error || '不可用'}`}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span>订单数据:</span>
                                        <span className={ctpStatus.data_availability.orders?.success ? 'success' : 'error'}>
                                            {ctpStatus.data_availability.orders?.success
                                                ? `✅ ${ctpStatus.data_availability.orders.count}个订单`
                                                : `❌ ${ctpStatus.data_availability.orders?.error || '不可用'}`}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span>成交数据:</span>
                                        <span className={ctpStatus.data_availability.trades?.success ? 'success' : 'error'}>
                                            {ctpStatus.data_availability.trades?.success
                                                ? `✅ ${ctpStatus.data_availability.trades.count}个成交`
                                                : `❌ ${ctpStatus.data_availability.trades?.error || '不可用'}`}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span>账户数据:</span>
                                        <span className={ctpStatus.data_availability.account?.success ? 'success' : 'error'}>
                                            {ctpStatus.data_availability.account?.success
                                                ? `✅ ${ctpStatus.data_availability.account.has_data ? '有数据' : '无数据'}`
                                                : `❌ ${ctpStatus.data_availability.account?.error || '不可用'}`}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* 建议 */}
                            {ctpStatus.suggestions && ctpStatus.suggestions.length > 0 && (
                                <div className="suggestions">
                                    <h4>建议</h4>
                                    <ul>
                                        {ctpStatus.suggestions.map((suggestion: string, index: number) => (
                                            <li key={index}>{suggestion}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* 调试信息面板 */}
            {showDebugInfo && (
                <div className="debug-panel">
                    <h3>调试信息</h3>
                    <div className="debug-content">
                        <div className="debug-section">
                            <h4>数据状态</h4>
                            <p>持仓数量: {positions.length}</p>
                            <p>订单数量: {orders.length}</p>
                            <p>成交数量: {trades.length}</p>
                            <p>算法订单数量: {algoOrders.length}</p>
                            <p>账户信息: {accountInfo ? '有' : '无'}</p>
                            <p>最后刷新: {lastRefresh.toLocaleString()}</p>
                        </div>

                        <div className="debug-section">
                            <h4>WebSocket状态</h4>
                            <p>连接状态: {isConnected ? '已连接' : '未连接'}</p>
                            <p>最后消息: {lastMessage ? JSON.stringify(lastMessage).substring(0, 100) + '...' : '无'}</p>
                        </div>

                        {ctpStatus && (
                            <div className="debug-section">
                                <h4>CTP详细状态</h4>
                                <pre>{JSON.stringify(ctpStatus, null, 2)}</pre>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* 统计概览 */}
            <div className="trading-statistics">
                <div className="stat-item">
                    <span className="stat-label">持仓</span>
                    <span className="stat-value">{statisticsSummary.totalPositions}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">总盈亏</span>
                    <span className={`stat-value ${statisticsSummary.totalPnl >= 0 ? 'profit' : 'loss'}`}>
                        {statisticsSummary.totalPnl.toFixed(2)}
                    </span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">保证金</span>
                    <span className="stat-value">{statisticsSummary.totalMargin.toFixed(2)}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">活跃订单</span>
                    <span className="stat-value">{statisticsSummary.activeOrders}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">算法订单</span>
                    <span className="stat-value">{statisticsSummary.runningAlgoOrders}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">今日成交</span>
                    <span className="stat-value">{statisticsSummary.todayTrades}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">最后更新</span>
                    <span className="stat-value">{lastRefresh.toLocaleTimeString()}</span>
                </div>
            </div>

            {/* 主要内容区 */}
            <div className="trading-panel-content">
                {/* 左侧：交易操作面板 */}
                <div className="trading-controls">
                    <div className="trading-tabs">
                        <button
                            className={`tab-button ${activeTab === 'manual' ? 'active' : ''}`}
                            onClick={() => setActiveTab('manual')}
                        >
                            手动交易
                        </button>
                        <button
                            className={`tab-button ${activeTab === 'algo' ? 'active' : ''}`}
                            onClick={() => setActiveTab('algo')}
                        >
                            算法交易
                        </button>
                    </div>

                    <div className="trading-content">
                        {activeTab === 'manual' ? (
                            <ManualTradingPanel
                                positions={positions}
                                onRefresh={loadPositions}
                                tradingEnabled={tradingEnabled}
                            />
                        ) : (
                            <AlgoTradingPanel
                                algoOrders={algoOrders}
                                onRefresh={loadAlgoOrders}
                                tradingEnabled={tradingEnabled}
                            />
                        )}
                    </div>
                </div>

                {/* 右侧：信息展示面板 */}
                <div className="trading-info">
                    <div className="info-tabs">
                        <button
                            className={`tab-button ${infoTab === 'account' ? 'active' : ''}`}
                            onClick={() => setInfoTab('account')}
                        >
                            账户信息
                        </button>
                        <button
                            className={`tab-button ${infoTab === 'positions' ? 'active' : ''}`}
                            onClick={() => setInfoTab('positions')}
                        >
                            持仓({positions.length})
                        </button>
                        <button
                            className={`tab-button ${infoTab === 'orders' ? 'active' : ''}`}
                            onClick={() => setInfoTab('orders')}
                        >
                            订单({orders.length})
                        </button>
                        <button
                            className={`tab-button ${infoTab === 'algo-orders' ? 'active' : ''}`}
                            onClick={() => setInfoTab('algo-orders')}
                        >
                            算法订单({algoOrders.length})
                        </button>
                        <button
                            className={`tab-button ${infoTab === 'trades' ? 'active' : ''}`}
                            onClick={() => setInfoTab('trades')}
                        >
                            成交({trades.length})
                        </button>
                        <button
                            className={`tab-button ${infoTab === 'statistics' ? 'active' : ''}`}
                            onClick={() => setInfoTab('statistics')}
                        >
                            统计分析
                        </button>
                    </div>

                    <div className="info-content">
                        {infoTab === 'account' && (
                            <AccountPanel
                                accountInfo={accountInfo}
                                statistics={statistics}
                                onRefresh={loadAccountInfo}
                            />
                        )}
                        {infoTab === 'positions' && (
                            <PositionsTable
                                positions={positions}
                                onRefresh={loadPositions}
                            />
                        )}
                        {infoTab === 'orders' && (
                            <OrdersTable
                                orders={orders}
                                onRefresh={loadOrders}
                            />
                        )}
                        {infoTab === 'algo-orders' && (
                            <AlgoOrdersTable
                                algoOrders={algoOrders}
                                onRefresh={loadAlgoOrders}
                            />
                        )}
                        {infoTab === 'trades' && (
                            <TradesTable
                                trades={trades}
                                onRefresh={loadTrades}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* 加载状态 */}
            {isLoading && (
                <div className="loading-overlay">
                    <div className="loading-spinner">加载中...</div>
                </div>
            )}
        </div>
    );
};

export default React.memo(TradingPanel); 