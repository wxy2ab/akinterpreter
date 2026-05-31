import {
    AccountBookOutlined,
    BarChartOutlined,
    DatabaseOutlined,
    DeleteOutlined,
    LineChartOutlined,
    ReloadOutlined,
    SettingOutlined,
    TransactionOutlined
} from '@ant-design/icons';
import {
    Badge,
    Button,
    Col,
    Layout,
    Row,
    Space,
    Spin,
    Statistic,
    Tabs,
    Tag,
    Typography
} from 'antd';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './TradingPanelOptimized.css';

import { useWebSocket } from '../../context/WebSocketContext';
import AccountPanel from './AccountPanel';
import AlgoTradingPanel from './AlgoTradingPanel';
import ManualTradingPanel from './ManualTradingPanel';
import OrdersTable from './OrdersTable';
import PositionsTable from './PositionsTable';
import TradesTable from './TradesTable';
import TradingStatisticsPanel from './TradingStatisticsPanel';

const { Title, Text } = Typography;
const { Content } = Layout;

// 数据接口定义
interface Position {
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

const TradingPanelOptimized: React.FC = () => {
    // 状态管理
    const [positions, setPositions] = useState<Position[]>([]);
    const [orders, setOrders] = useState<any[]>([]);
    const [algoOrders, setAlgoOrders] = useState<any[]>([]);
    const [trades, setTrades] = useState<any[]>([]);
    const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
    const [statistics, setStatistics] = useState<TradingStatistics | null>(null);

    const [isLoading, setIsLoading] = useState(false);
    const [tradingEnabled, setTradingEnabled] = useState(true);
    const [riskControlEnabled, setRiskControlEnabled] = useState(true);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

    // WebSocket连接
    const { isConnected, sendMessage } = useWebSocket();

    // 初始化数据加载
    useEffect(() => {
        loadInitialData();
    }, []);



    // 数据加载函数
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

    const loadPositions = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/positions');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setPositions(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载持仓数据失败:', error);
            setPositions([]);
        }
    }, []);

    const loadOrders = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/orders?limit=50');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setOrders(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载订单数据失败:', error);
            setOrders([]);
        }
    }, []);

    const loadAlgoOrders = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/algo-orders?limit=30');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setAlgoOrders(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载算法订单失败:', error);
            setAlgoOrders([]);
        }
    }, []);

    const loadTrades = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/trades?limit=50');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setTrades(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('加载成交数据失败:', error);
            setTrades([]);
        }
    }, []);

    const loadAccountInfo = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/account');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setAccountInfo(data);
        } catch (error) {
            console.error('加载账户信息失败:', error);
            setAccountInfo(null);
        }
    }, []);

    const loadStatistics = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/statistics');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setStatistics(data);
        } catch (error) {
            console.error('加载统计数据失败:', error);
            setStatistics(null);
        }
    }, []);

    const loadTradingStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-management/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setTradingEnabled(data.trading_enabled);
            setRiskControlEnabled(data.risk_control_enabled);
        } catch (error) {
            console.error('加载交易状态失败:', error);
        }
    }, []);

    // 操作函数
    const handleRefresh = useCallback(() => {
        loadInitialData();
    }, [loadInitialData]);

    const handleInitTestData = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/trading-management/test-data/initialize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                await loadInitialData();
                console.log('测试数据初始化成功');
            } else {
                console.error('初始化测试数据失败');
            }
        } catch (error) {
            console.error('初始化测试数据失败:', error);
        } finally {
            setIsLoading(false);
        }
    }, [loadInitialData]);

    const handleClearTestData = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/trading-management/test-data/clear', {
                method: 'DELETE'
            });

            if (response.ok) {
                await loadInitialData();
                console.log('测试数据清除成功');
            } else {
                console.error('清除测试数据失败');
            }
        } catch (error) {
            console.error('清除测试数据失败:', error);
        } finally {
            setIsLoading(false);
        }
    }, [loadInitialData]);

    // 计算统计数据
    const summaryStats = useMemo(() => {
        const totalPnl = positions.reduce((sum, pos) => sum + (pos.positionPnl || 0) + (pos.closePnl || 0), 0);
        const totalMargin = positions.reduce((sum, pos) => sum + (pos.margin || 0), 0);

        return {
            totalPositions: positions.length,
            totalPnl,
            totalMargin,
            longPositions: positions.filter(p => p.direction === 'LONG').length,
            shortPositions: positions.filter(p => p.direction === 'SHORT').length,
        };
    }, [positions]);

    return (
        <Content style={{ padding: '0', height: 'calc(100vh - 112px)', overflow: 'hidden' }}>
            <Spin spinning={isLoading} tip="加载中...">
                <Layout style={{ height: '100%' }}>
                    {/* 顶部状态栏 */}
                    <div style={{
                        background: '#fff',
                        padding: '16px 24px',
                        borderBottom: '1px solid #f0f0f0',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                                <TransactionOutlined /> 交易管理
                            </Title>
                            <Badge
                                status={isConnected ? 'success' : 'error'}
                                text={isConnected ? 'WebSocket已连接' : 'WebSocket断开'}
                            />
                            <Tag color={tradingEnabled ? 'green' : 'red'}>
                                交易{tradingEnabled ? '启用' : '禁用'}
                            </Tag>
                            <Tag color={riskControlEnabled ? 'blue' : 'orange'}>
                                风控{riskControlEnabled ? '启用' : '禁用'}
                            </Tag>
                        </div>

                        <Space>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={handleRefresh}
                                loading={isLoading}
                            >
                                刷新
                            </Button>
                            <Button
                                icon={<DatabaseOutlined />}
                                onClick={handleInitTestData}
                                loading={isLoading}
                            >
                                测试数据
                            </Button>
                            <Button
                                icon={<DeleteOutlined />}
                                onClick={handleClearTestData}
                                loading={isLoading}
                                danger
                            >
                                清除数据
                            </Button>
                        </Space>
                    </div>

                    {/* 统计概览 */}
                    <div style={{
                        background: '#fff',
                        padding: '16px 24px',
                        borderBottom: '1px solid #f0f0f0'
                    }}>
                        <Row gutter={24}>
                            <Col span={4}>
                                <Statistic
                                    title="持仓数量"
                                    value={summaryStats.totalPositions}
                                    prefix={<LineChartOutlined />}
                                />
                            </Col>
                            <Col span={4}>
                                <Statistic
                                    title="多仓"
                                    value={summaryStats.longPositions}
                                    valueStyle={{ color: '#f56a00' }}
                                />
                            </Col>
                            <Col span={4}>
                                <Statistic
                                    title="空仓"
                                    value={summaryStats.shortPositions}
                                    valueStyle={{ color: '#722ed1' }}
                                />
                            </Col>
                            <Col span={4}>
                                <Statistic
                                    title="总盈亏"
                                    value={summaryStats.totalPnl}
                                    precision={2}
                                    valueStyle={{ color: summaryStats.totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
                                    suffix="元"
                                />
                            </Col>
                            <Col span={4}>
                                <Statistic
                                    title="保证金"
                                    value={summaryStats.totalMargin}
                                    precision={2}
                                    suffix="元"
                                />
                            </Col>
                            <Col span={4}>
                                <Statistic
                                    title="账户余额"
                                    value={accountInfo?.balance || 0}
                                    precision={2}
                                    prefix={<AccountBookOutlined />}
                                    suffix="元"
                                />
                            </Col>
                        </Row>
                    </div>

                    {/* 主要内容区域 */}
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                        <Row style={{ height: '100%' }} gutter={0}>
                            {/* 左侧交易操作区 */}
                            <Col span={8} style={{ height: '100%', borderRight: '1px solid #f0f0f0' }}>
                                <Tabs
                                    defaultActiveKey="manual"
                                    style={{ height: '100%' }}
                                    items={[
                                        {
                                            key: 'manual',
                                            label: (
                                                <span>
                                                    <TransactionOutlined />
                                                    手动交易
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ padding: '16px', height: 'calc(100vh - 260px)', overflow: 'auto' }}>
                                                    <ManualTradingPanel
                                                        positions={positions}
                                                        onRefresh={loadPositions}
                                                        tradingEnabled={tradingEnabled}
                                                    />
                                                </div>
                                            )
                                        },
                                        {
                                            key: 'algo',
                                            label: (
                                                <span>
                                                    <BarChartOutlined />
                                                    算法交易
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ padding: '16px', height: 'calc(100vh - 260px)', overflow: 'auto' }}>
                                                    <AlgoTradingPanel
                                                        algoOrders={algoOrders}
                                                        onRefresh={loadAlgoOrders}
                                                        tradingEnabled={tradingEnabled}
                                                    />
                                                </div>
                                            )
                                        }
                                    ]}
                                />
                            </Col>

                            {/* 右侧数据展示区 */}
                            <Col span={16} style={{ height: '100%' }}>
                                <Tabs
                                    defaultActiveKey="positions"
                                    style={{ height: '100%' }}
                                    items={[
                                        {
                                            key: 'positions',
                                            label: (
                                                <span>
                                                    <LineChartOutlined />
                                                    持仓 ({positions.length})
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto' }}>
                                                    <PositionsTable
                                                        positions={positions}
                                                        onRefresh={loadPositions}
                                                    />
                                                </div>
                                            )
                                        },
                                        {
                                            key: 'orders',
                                            label: (
                                                <span>
                                                    <SettingOutlined />
                                                    订单 ({orders.length})
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto' }}>
                                                    <OrdersTable
                                                        orders={orders}
                                                        onRefresh={loadOrders}
                                                    />
                                                </div>
                                            )
                                        },
                                        {
                                            key: 'trades',
                                            label: (
                                                <span>
                                                    <TransactionOutlined />
                                                    成交 ({trades.length})
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto' }}>
                                                    <TradesTable
                                                        trades={trades}
                                                        onRefresh={loadTrades}
                                                    />
                                                </div>
                                            )
                                        },
                                        {
                                            key: 'account',
                                            label: (
                                                <span>
                                                    <AccountBookOutlined />
                                                    账户
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto', padding: '16px' }}>
                                                    {statistics ? (
                                                        <AccountPanel
                                                            accountInfo={accountInfo}
                                                            statistics={statistics}
                                                            onRefresh={loadAccountInfo}
                                                        />
                                                    ) : (
                                                        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                                            加载统计数据中...
                                                        </div>
                                                    )}
                                                </div>
                                            )
                                        },
                                        {
                                            key: 'statistics',
                                            label: (
                                                <span>
                                                    <BarChartOutlined />
                                                    统计
                                                </span>
                                            ),
                                            children: (
                                                <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto', padding: '16px' }}>
                                                    <TradingStatisticsPanel />
                                                </div>
                                            )
                                        }
                                    ]}
                                />
                            </Col>
                        </Row>
                    </div>

                    {/* 底部状态栏 */}
                    {lastRefresh && (
                        <div style={{
                            background: '#fafafa',
                            padding: '8px 24px',
                            borderTop: '1px solid #f0f0f0',
                            fontSize: '12px',
                            color: '#666'
                        }}>
                            最后更新: {lastRefresh.toLocaleString()} |
                            持仓: {positions.length} |
                            订单: {orders.length} |
                            成交: {trades.length}
                        </div>
                    )}
                </Layout>
            </Spin>
        </Content>
    );
};

export default React.memo(TradingPanelOptimized); 