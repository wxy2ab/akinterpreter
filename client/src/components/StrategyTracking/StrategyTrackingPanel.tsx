import {
    ClearOutlined,
    DownloadOutlined,
    LineChartOutlined,
    ReloadOutlined,
    SignalFilled,
    TrophyOutlined
} from '@ant-design/icons';
import {
    Badge,
    Button,
    Card,
    Col,
    message,
    Popconfirm,
    Row,
    Space,
    Spin,
    Statistic,
    Tabs
} from 'antd';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { StrategySignalsTable } from './StrategySignalsTable';
import { StrategyStatisticsTable } from './StrategyStatisticsTable';
import './StrategyTrackingPanel.css';
import { TrackingFilter } from './TrackingFilter';
import { TradeExecutionsTable } from './TradeExecutionsTable';

const { TabPane } = Tabs;

// 数据接口定义
export interface StrategySignal {
    signal_id: string;
    timestamp: string;
    strategy_name: string;
    symbol: string;
    signal_type: string;
    alpha_value: number;
    price: number;
    quantity: number;
    confidence: number;
    status: string;
}

export interface TradeExecution {
    trade_id: string;
    timestamp: string;
    strategy_name: string;
    symbol: string;
    direction: string;
    price: number;
    quantity: number;
    filled_quantity: number;
    status: string;
    pnl: number;
    notes: string;
    order_id: string;
}

export interface StrategyStatistics {
    strategy_name: string;
    total_signals: number;
    success_signals: number;
    success_rate: number;
    total_profit: number;
    avg_profit: number;
    last_signal_time?: string;
}

export interface TrackingStats {
    total_signals: number;
    total_trades: number;
    total_strategies: number;
    active_strategies: number;
    total_profit: number;
    overall_success_rate: number;
    last_update: string;
}

// 过滤条件接口
export interface FilterParams {
    time_range_hours?: number;
    strategy_names?: string[];
    signal_types?: string[];
    symbols?: string[];
    execution_status?: string[];
    max_items?: number;
}

const StrategyTrackingPanel: React.FC = () => {
    // 状态管理
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('signals');
    const [signals, setSignals] = useState<StrategySignal[]>([]);
    const [trades, setTrades] = useState<TradeExecution[]>([]);
    const [statistics, setStatistics] = useState<StrategyStatistics[]>([]);
    const [trackingStats, setTrackingStats] = useState<TrackingStats>({
        total_signals: 0,
        total_trades: 0,
        total_strategies: 0,
        active_strategies: 0,
        total_profit: 0,
        overall_success_rate: 0,
        last_update: new Date().toISOString()
    });
    const [filterParams, setFilterParams] = useState<FilterParams>({
        time_range_hours: 24,
        max_items: 200
    });

    // WebSocket 连接
    const { isConnected, subscribe, unsubscribe, sendMessage } = useWebSocket();

    // API 请求函数
    const fetchSignals = useCallback(async (params: FilterParams = filterParams) => {
        try {
            setLoading(true);

            const queryParams = new URLSearchParams();
            if (params.time_range_hours) queryParams.append('time_range_hours', params.time_range_hours.toString());
            if (params.strategy_names?.length) queryParams.append('strategy_names', params.strategy_names.join(','));
            if (params.signal_types?.length) queryParams.append('signal_types', params.signal_types.join(','));
            if (params.symbols?.length) queryParams.append('symbols', params.symbols.join(','));
            if (params.max_items) queryParams.append('max_items', params.max_items.toString());

            const response = await fetch(`/api/strategy-tracking/signals?${queryParams}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                setSignals(result.data || []);
            } else {
                throw new Error(result.message || '获取策略信号失败');
            }
        } catch (error) {
            console.error('获取策略信号失败:', error);
            message.error(`获取策略信号失败: ${error instanceof Error ? error.message : String(error)}`);
            setSignals([]); // 清空数据，显示真实错误状态
        } finally {
            setLoading(false);
        }
    }, [filterParams]);

    const fetchTrades = useCallback(async (params: FilterParams = filterParams) => {
        try {
            setLoading(true);

            const queryParams = new URLSearchParams();
            if (params.time_range_hours) queryParams.append('time_range_hours', params.time_range_hours.toString());
            if (params.strategy_names?.length) queryParams.append('strategy_names', params.strategy_names.join(','));
            if (params.execution_status?.length) queryParams.append('execution_status', params.execution_status.join(','));
            if (params.symbols?.length) queryParams.append('symbols', params.symbols.join(','));
            if (params.max_items) queryParams.append('max_items', params.max_items.toString());

            const response = await fetch(`/api/strategy-tracking/trades?${queryParams}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                setTrades(result.data || []);
            } else {
                throw new Error(result.message || '获取交易执行失败');
            }
        } catch (error) {
            console.error('获取交易执行失败:', error);
            message.error(`获取交易执行失败: ${error instanceof Error ? error.message : String(error)}`);
            setTrades([]); // 清空数据，显示真实错误状态
        } finally {
            setLoading(false);
        }
    }, [filterParams]);

    const fetchStatistics = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-tracking/statistics');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                setStatistics(result.data || []);
            } else {
                throw new Error(result.message || '获取策略统计失败');
            }
        } catch (error) {
            console.error('获取策略统计失败:', error);
            message.error(`获取策略统计失败: ${error instanceof Error ? error.message : String(error)}`);
            setStatistics([]); // 清空数据，显示真实错误状态
        }
    }, []);

    const fetchTrackingStats = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-tracking/stats');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                setTrackingStats(result.data);
            } else {
                throw new Error(result.message || '获取追踪统计失败');
            }
        } catch (error) {
            console.error('获取追踪统计失败:', error);
            message.error(`获取追踪统计失败: ${error instanceof Error ? error.message : String(error)}`);
            setTrackingStats({
                total_signals: 0,
                total_trades: 0,
                total_strategies: 0,
                active_strategies: 0,
                total_profit: 0,
                overall_success_rate: 0,
                last_update: new Date().toISOString()
            }); // 使用默认值而不是null
        }
    }, []);

    // 清空数据
    const clearAllData = useCallback(async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/strategy-tracking/clear', { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                message.success('数据清空成功');
                // 重新加载数据
                await Promise.all([
                    fetchSignals(),
                    fetchTrades(),
                    fetchStatistics(),
                    fetchTrackingStats()
                ]);
            } else {
                message.error('数据清空失败');
            }
        } catch (error) {
            console.error('Error clearing data:', error);
            message.error('数据清空失败');
        } finally {
            setLoading(false);
        }
    }, [fetchSignals, fetchTrades, fetchStatistics, fetchTrackingStats]);

    // 导出数据
    const exportData = useCallback(async (type: 'signals' | 'trades', format: 'csv' | 'json' = 'csv') => {
        try {
            const queryParams = new URLSearchParams();
            if (filterParams.time_range_hours) queryParams.append('time_range_hours', filterParams.time_range_hours.toString());
            if (filterParams.strategy_names?.length) queryParams.append('strategy_names', filterParams.strategy_names.join(','));
            if (type === 'signals' && filterParams.signal_types?.length) {
                queryParams.append('signal_types', filterParams.signal_types.join(','));
            }
            if (type === 'trades' && filterParams.execution_status?.length) {
                queryParams.append('execution_status', filterParams.execution_status.join(','));
            }
            if (filterParams.symbols?.length) queryParams.append('symbols', filterParams.symbols.join(','));
            queryParams.append('format', format);

            const response = await fetch(`/api/strategy-tracking/export/${type}?${queryParams}`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;

                const contentDisposition = response.headers.get('Content-Disposition');
                const filename = contentDisposition
                    ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
                    : `${type}_${new Date().toISOString().slice(0, 10)}.${format}`;

                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);

                message.success('导出成功');
            } else {
                message.error('导出失败');
            }
        } catch (error) {
            console.error('Error exporting data:', error);
            message.error('导出失败');
        }
    }, [filterParams]);

    // WebSocket 事件处理
    const handleWebSocketMessage = useCallback((data: any) => {
        if (data.type === 'strategy_signal') {
            // 实时更新策略信号
            setSignals(prev => [data.data, ...prev.slice(0, (filterParams.max_items || 200) - 1)]);
        } else if (data.type === 'trade_execution') {
            // 实时更新交易执行
            setTrades(prev => [data.data, ...prev.slice(0, (filterParams.max_items || 200) - 1)]);
        } else if (data.type === 'tracking_statistics') {
            // 实时更新统计信息
            setTrackingStats(data.data);
        }
    }, [filterParams.max_items]);

    // 过滤条件变更处理
    const handleFilterChange = useCallback((newParams: FilterParams) => {
        setFilterParams(newParams);
    }, []);

    // 刷新数据
    const refreshData = useCallback(() => {
        if (activeTab === 'signals') {
            fetchSignals();
        } else if (activeTab === 'trades') {
            fetchTrades();
        } else if (activeTab === 'statistics') {
            fetchStatistics();
        }
        fetchTrackingStats();
    }, [activeTab, fetchSignals, fetchTrades, fetchStatistics, fetchTrackingStats]);

    // 初始化和数据加载
    useEffect(() => {
        Promise.all([
            fetchSignals(),
            fetchTrades(),
            fetchStatistics(),
            fetchTrackingStats()
        ]);
    }, []);

    // WebSocket 订阅
    useEffect(() => {
        if (isConnected) {
            subscribe(['strategy_tracking_update'], handleWebSocketMessage);
            return () => unsubscribe(['strategy_tracking_update']);
        }
    }, [isConnected, subscribe, unsubscribe, handleWebSocketMessage]);

    // 过滤参数变更时重新加载数据
    useEffect(() => {
        const timer = setTimeout(() => {
            if (activeTab === 'signals') {
                fetchSignals(filterParams);
            } else if (activeTab === 'trades') {
                fetchTrades(filterParams);
            }
        }, 500); // 防抖

        return () => clearTimeout(timer);
    }, [filterParams, activeTab, fetchSignals, fetchTrades]);

    // 计算统计数据
    const displayStats = useMemo(() => [
        {
            title: '策略信号',
            value: trackingStats.total_signals,
            suffix: '条',
            precision: 0,
            valueStyle: { color: '#1890ff' }
        },
        {
            title: '交易执行',
            value: trackingStats.total_trades,
            suffix: '笔',
            precision: 0,
            valueStyle: { color: '#52c41a' }
        },
        {
            title: '活跃策略',
            value: trackingStats.active_strategies,
            suffix: '个',
            precision: 0,
            valueStyle: { color: '#722ed1' }
        },
        {
            title: '总盈亏',
            value: trackingStats.total_profit,
            prefix: '¥',
            precision: 2,
            valueStyle: { color: trackingStats.total_profit >= 0 ? '#52c41a' : '#ff4d4f' }
        },
        {
            title: '成功率',
            value: trackingStats.overall_success_rate,
            suffix: '%',
            precision: 1,
            valueStyle: { color: trackingStats.overall_success_rate >= 50 ? '#52c41a' : '#ff4d4f' }
        }
    ], [trackingStats]);

    return (
        <div className="strategy-tracking-panel">
            <Card
                title={
                    <Space>
                        <SignalFilled />
                        策略追踪
                        <Badge count={trackingStats.total_signals} showZero color="#1890ff" />
                    </Space>
                }
                extra={
                    <Space>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={refreshData}
                            loading={loading}
                            size="small"
                        >
                            刷新
                        </Button>
                        <Popconfirm
                            title="确定要清空所有追踪数据吗？"
                            onConfirm={clearAllData}
                            okText="确定"
                            cancelText="取消"
                        >
                            <Button
                                icon={<ClearOutlined />}
                                danger
                                size="small"
                            >
                                清空
                            </Button>
                        </Popconfirm>
                    </Space>
                }
                className="strategy-tracking-card"
            >
                {/* 统计概览 */}
                <Row gutter={16} style={{ marginBottom: 16 }}>
                    {displayStats.map((stat, index) => (
                        <Col span={4.8} key={index}>
                            <Statistic
                                title={stat.title}
                                value={stat.value}
                                precision={stat.precision}
                                prefix={stat.prefix}
                                suffix={stat.suffix}
                                valueStyle={stat.valueStyle}
                            />
                        </Col>
                    ))}
                </Row>

                {/* 过滤器 */}
                <TrackingFilter
                    filterParams={filterParams}
                    onFilterChange={handleFilterChange}
                    signals={signals}
                    trades={trades}
                />

                {/* 主要内容选项卡 */}
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    tabBarExtraContent={
                        <Space>
                            {activeTab === 'signals' && (
                                <Button
                                    icon={<DownloadOutlined />}
                                    size="small"
                                    onClick={() => exportData('signals')}
                                >
                                    导出信号
                                </Button>
                            )}
                            {activeTab === 'trades' && (
                                <Button
                                    icon={<DownloadOutlined />}
                                    size="small"
                                    onClick={() => exportData('trades')}
                                >
                                    导出交易
                                </Button>
                            )}
                        </Space>
                    }
                >
                    <TabPane
                        tab={
                            <span>
                                <SignalFilled />
                                策略信号 <Badge count={signals.length} showZero />
                            </span>
                        }
                        key="signals"
                    >
                        <Spin spinning={loading}>
                            <StrategySignalsTable
                                signals={signals}
                                loading={loading}
                                filterParams={filterParams}
                            />
                        </Spin>
                    </TabPane>

                    <TabPane
                        tab={
                            <span>
                                <TrophyOutlined />
                                交易执行 <Badge count={trades.length} showZero />
                            </span>
                        }
                        key="trades"
                    >
                        <Spin spinning={loading}>
                            <TradeExecutionsTable
                                trades={trades}
                                loading={loading}
                                filterParams={filterParams}
                            />
                        </Spin>
                    </TabPane>

                    <TabPane
                        tab={
                            <span>
                                <LineChartOutlined />
                                策略统计 <Badge count={statistics.length} showZero />
                            </span>
                        }
                        key="statistics"
                    >
                        <Spin spinning={loading}>
                            <StrategyStatisticsTable
                                statistics={statistics}
                                loading={loading}
                            />
                        </Spin>
                    </TabPane>
                </Tabs>
            </Card>
        </div>
    );
};

export default StrategyTrackingPanel; 