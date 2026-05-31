import {
    AlertOutlined,
    BarChartOutlined,
    CaretDownOutlined,
    CaretUpOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ExclamationCircleOutlined,
    EyeOutlined,
    PlayCircleOutlined,
    ReloadOutlined,
    SettingOutlined,
    SignalFilled
} from '@ant-design/icons';
import {
    Alert,
    Badge,
    Button,
    Card,
    Col,
    Descriptions,
    Divider,
    Drawer,
    Form,
    message,
    Progress,
    Row,
    Select,
    Space,
    Statistic,
    Switch,
    Table,
    Tabs,
    Tag,
    Timeline,
    Typography
} from 'antd';
import React, { useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useWebSocket } from '../../context/WebSocketContext';
import { RootState } from '../../store/store';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

// 策略信号数据接口
interface StrategySignal {
    signal_id: string;
    strategy_name: string;
    symbol: string;
    signal_type: 'buy' | 'sell' | 'hold';
    signal_strength: number;
    alpha_value: number;
    timestamp: string;
    current_price: number;
    target_price?: number;
    stop_loss?: number;
    position_size: number;
    status: 'pending' | 'executed' | 'cancelled' | 'expired';
    execution_price?: number;
    execution_time?: string;
    reason?: string;
}

// 策略性能数据接口
interface StrategyPerformance {
    strategy_name: string;
    total_signals: number;
    successful_signals: number;
    success_rate: number;
    total_pnl: number;
    win_rate: number;
    avg_win: number;
    avg_loss: number;
    max_drawdown: number;
    sharpe_ratio: number;
    last_update: string;
}

// 策略状态接口
interface StrategyStatus {
    name: string;
    enabled: boolean;
    symbols: string[];
    alpha_threshold: number;
    position_multiplier: number;
    greed_position: boolean;
    freq: string;
    init_bars: number;
    status: 'running' | 'stopped' | 'error';
    last_signal_time?: string;
    total_signals?: number;
    active_positions?: number;
    error_message?: string;
}

const StrategyPage: React.FC = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [selectedStrategy, setSelectedStrategy] = useState<string>('');
    const [signalDrawerVisible, setSignalDrawerVisible] = useState(false);
    const [configModalVisible, setConfigModalVisible] = useState(false);
    const [selectedSignal, setSelectedSignal] = useState<StrategySignal | null>(null);

    const dispatch = useDispatch();
    const { isConnected, sendMessage } = useWebSocket();

    // 从Redux store获取系统日志
    const systemLogs = useSelector((state: RootState) => state.system.logs);

    // 直接从API加载策略数据
    const [strategies, setStrategies] = useState<Record<string, any>>({});
    const [signals, setSignals] = useState<StrategySignal[]>([]);
    const [performances, setPerformances] = useState<Record<string, StrategyPerformance>>({});

    console.log('StrategyPage - Strategies from API:', strategies);
    console.log('StrategyPage - Signals:', signals);

    // 转换API数据为策略状态列表
    const strategyList: StrategyStatus[] = Object.values(strategies).map(strategy => ({
        name: strategy.name,
        enabled: strategy.enabled,
        symbols: strategy.symbols || [],
        alpha_threshold: strategy.alpha_threshold,
        position_multiplier: strategy.position_multiplier,
        greed_position: strategy.greed_position,
        freq: strategy.freq,
        init_bars: strategy.init_bars,
        status: strategy.enabled ? 'running' : 'stopped',
        last_signal_time: strategy.last_signal_time,
        total_signals: strategy.total_signals,
        active_positions: 0 // 需要从持仓数据计算
    }));

    // 加载策略数据
    const loadStrategies = useCallback(async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/strategy-management/strategies');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // 转换为Record格式
                    const strategiesRecord: Record<string, any> = {};
                    result.data.forEach((strategy: any) => {
                        strategiesRecord[strategy.name] = strategy;
                    });
                    setStrategies(strategiesRecord);
                } else {
                    console.error('获取策略列表失败:', result.message);
                }
            } else {
                console.error('获取策略列表失败:', response.statusText);
            }
        } catch (error) {
            console.error('加载策略数据失败:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // 加载信号数据
    const loadSignals = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-tracking/signals?time_range_hours=24&max_items=50');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // 转换信号数据格式
                    const convertedSignals: StrategySignal[] = result.data.map((signal: any) => ({
                        signal_id: signal.signal_id,
                        strategy_name: signal.strategy_name,
                        symbol: signal.symbol,
                        signal_type: signal.signal_type === 'buy' ? 'buy' : signal.signal_type === 'sell' ? 'sell' : 'hold',
                        signal_strength: signal.confidence || 0.5,
                        alpha_value: signal.alpha_value || 0,
                        timestamp: signal.timestamp,
                        current_price: signal.price || 0,
                        target_price: signal.price || 0,
                        stop_loss: signal.price || 0,
                        position_size: signal.quantity || 1,
                        status: signal.status === 'Executed' ? 'executed' :
                            signal.status === 'Pending' ? 'pending' :
                                signal.status === 'Cancelled' ? 'cancelled' : 'expired',
                        execution_price: signal.price || 0,
                        execution_time: signal.timestamp,
                        reason: `Alpha值: ${signal.alpha_value}, 置信度: ${signal.confidence}`
                    }));
                    setSignals(convertedSignals);
                } else {
                    console.error('获取信号数据失败:', result.message);
                }
            } else {
                console.error('获取信号数据失败:', response.statusText);
            }
        } catch (error) {
            console.error('加载信号数据失败:', error);
        }
    }, []);

    // 组件挂载时加载数据
    useEffect(() => {
        loadStrategies();
        loadSignals();
    }, [loadStrategies, loadSignals]);

    // 订阅策略数据
    useEffect(() => {
        if (isConnected) {
            console.log('WebSocket已连接，订阅策略数据');
            sendMessage({
                type: 'subscribe',
                event_types: ['*']  // 订阅所有事件
            });

            // 请求最新数据
            sendMessage({
                type: 'get_latest_data',
                event_types: ['strategy_update', 'strategy_signal', 'strategy_performance']
            });
        }
    }, [isConnected, sendMessage]);

    // 定期刷新数据
    useEffect(() => {
        const interval = setInterval(() => {
            loadStrategies();
            loadSignals();
        }, 30000); // 每30秒刷新一次

        return () => clearInterval(interval);
    }, [loadStrategies, loadSignals]);

    // 切换策略启停状态
    const toggleStrategy = async (strategyName: string, enabled: boolean) => {
        try {
            const response = await fetch(`/api/strategy-management/strategies/${strategyName}/enable`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled }),
            });

            const result = await response.json();

            if (result.success) {
                message.success(`策略 ${strategyName} 已${enabled ? '启动' : '停止'}`);
                // 重新加载策略数据
                loadStrategies();
            } else {
                message.error(`操作失败: ${result.message}`);
            }
        } catch (error) {
            message.error('操作失败，请检查网络连接');
        }
    };

    // 执行策略信号
    const executeSignal = async (signal: StrategySignal) => {
        try {
            const response = await fetch('/api/strategy-management/execute-signal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    signal_id: signal.signal_id,
                    strategy_name: signal.strategy_name,
                    symbol: signal.symbol,
                    direction: signal.signal_type,
                    price: signal.current_price,
                    volume: signal.position_size
                }),
            });

            const result = await response.json();

            if (result.success) {
                message.success('信号执行成功');
                // 重新加载信号数据
                loadSignals();
            } else {
                message.error(`信号执行失败: ${result.message}`);
            }
        } catch (error) {
            message.error('信号执行失败，请检查网络连接');
        }
    };

    // 策略列表表格列定义
    const strategyColumns = [
        {
            title: '策略名称',
            dataIndex: 'name',
            key: 'name',
            width: 150,
            render: (name: string, record: StrategyStatus) => (
                <Space>
                    <Text strong>{name}</Text>
                    <Badge
                        status={record.status === 'running' ? 'processing' :
                            record.status === 'error' ? 'error' : 'default'}
                        text={record.status === 'running' ? '运行中' :
                            record.status === 'error' ? '错误' : '已停止'}
                    />
                </Space>
            ),
        },
        {
            title: '状态',
            dataIndex: 'enabled',
            key: 'enabled',
            width: 100,
            render: (enabled: boolean, record: StrategyStatus) => (
                <Switch
                    checked={enabled}
                    onChange={(checked) => toggleStrategy(record.name, checked)}
                    checkedChildren="启用"
                    unCheckedChildren="禁用"
                />
            ),
        },
        {
            title: '交易品种',
            dataIndex: 'symbols',
            key: 'symbols',
            width: 200,
            render: (symbols: string[]) => (
                <Space wrap>
                    {symbols.map(symbol => (
                        <Tag key={symbol} color="blue">{symbol}</Tag>
                    ))}
                </Space>
            ),
        },
        {
            title: '信号阈值',
            dataIndex: 'alpha_threshold',
            key: 'alpha_threshold',
            width: 100,
            render: (threshold: number) => threshold?.toFixed(2) || '--',
        },
        {
            title: '频率',
            dataIndex: 'freq',
            key: 'freq',
            width: 80,
        },
        {
            title: '总信号数',
            dataIndex: 'total_signals',
            key: 'total_signals',
            width: 100,
            render: (count: number) => count || 0,
        },
        {
            title: '最后信号',
            dataIndex: 'last_signal_time',
            key: 'last_signal_time',
            width: 150,
            render: (time: string) => time ? new Date(time).toLocaleString() : '--',
        },
        {
            title: '操作',
            key: 'action',
            width: 200,
            render: (_: any, record: StrategyStatus) => (
                <Space>
                    <Button
                        type="link"
                        icon={<EyeOutlined />}
                        onClick={() => setSelectedStrategy(record.name)}
                    >
                        详情
                    </Button>
                    <Button
                        type="link"
                        icon={<SettingOutlined />}
                        onClick={() => {
                            setSelectedStrategy(record.name);
                            setConfigModalVisible(true);
                        }}
                    >
                        配置
                    </Button>
                    <Button
                        type="link"
                        icon={<BarChartOutlined />}
                        onClick={() => {
                            setSelectedStrategy(record.name);
                            // 打开性能分析页面
                        }}
                    >
                        性能
                    </Button>
                </Space>
            ),
        },
    ];

    // 信号列表表格列定义
    const signalColumns = [
        {
            title: '信号ID',
            dataIndex: 'signal_id',
            key: 'signal_id',
            width: 100,
            render: (id: string) => (
                <Text code>{id.slice(-6)}</Text>
            ),
        },
        {
            title: '策略',
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 120,
        },
        {
            title: '品种',
            dataIndex: 'symbol',
            key: 'symbol',
            width: 100,
        },
        {
            title: '信号类型',
            dataIndex: 'signal_type',
            key: 'signal_type',
            width: 100,
            render: (type: string, record: StrategySignal) => {
                const color = type === 'buy' ? 'red' : type === 'sell' ? 'green' : 'blue';
                const icon = type === 'buy' ? <CaretUpOutlined /> :
                    type === 'sell' ? <CaretDownOutlined /> : <SignalFilled />;
                return (
                    <Tag color={color} icon={icon}>
                        {type === 'buy' ? '做多' : type === 'sell' ? '做空' : '持有'}
                    </Tag>
                );
            },
        },
        {
            title: '信号强度',
            dataIndex: 'signal_strength',
            key: 'signal_strength',
            width: 120,
            render: (strength: number) => (
                <Progress
                    percent={strength * 100}
                    size="small"
                    status={strength > 0.7 ? 'active' : 'normal'}
                    format={() => `${(strength * 100).toFixed(0)}%`}
                />
            ),
        },
        {
            title: 'Alpha值',
            dataIndex: 'alpha_value',
            key: 'alpha_value',
            width: 100,
            render: (alpha: number) => (
                <Text style={{ color: alpha > 0 ? '#f5222d' : alpha < 0 ? '#52c41a' : '#666' }}>
                    {alpha?.toFixed(3) || '--'}
                </Text>
            ),
        },
        {
            title: '当前价格',
            dataIndex: 'current_price',
            key: 'current_price',
            width: 100,
            render: (price: number) => price?.toFixed(2) || '--',
        },
        {
            title: '仓位',
            dataIndex: 'position_size',
            key: 'position_size',
            width: 80,
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => {
                const statusMap = {
                    'pending': { color: 'processing', text: '待执行', icon: <ExclamationCircleOutlined /> },
                    'executed': { color: 'success', text: '已执行', icon: <CheckCircleOutlined /> },
                    'cancelled': { color: 'default', text: '已取消', icon: <CloseCircleOutlined /> },
                    'expired': { color: 'warning', text: '已过期', icon: <AlertOutlined /> }
                };
                const config = statusMap[status as keyof typeof statusMap] || statusMap.pending;
                return (
                    <Badge status={config.color as any} text={
                        <Space>
                            {config.icon}
                            {config.text}
                        </Space>
                    } />
                );
            },
        },
        {
            title: '时间',
            dataIndex: 'timestamp',
            key: 'timestamp',
            width: 150,
            render: (time: string) => new Date(time).toLocaleString(),
        },
        {
            title: '操作',
            key: 'action',
            width: 150,
            render: (_: any, record: StrategySignal) => (
                <Space>
                    <Button
                        type="link"
                        size="small"
                        onClick={() => {
                            setSelectedSignal(record);
                            setSignalDrawerVisible(true);
                        }}
                    >
                        详情
                    </Button>
                    {record.status === 'pending' && (
                        <Button
                            type="link"
                            size="small"
                            onClick={() => executeSignal(record)}
                        >
                            执行
                        </Button>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>策略管理</Title>

            {/* 策略概览统计 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="策略总数"
                            value={strategyList.length}
                            prefix={<SettingOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="运行中策略"
                            value={strategyList.filter(s => s.enabled).length}
                            valueStyle={{ color: '#3f8600' }}
                            prefix={<PlayCircleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="今日信号数"
                            value={signals.length}
                            prefix={<SignalFilled />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="待执行信号"
                            value={signals.filter(s => s.status === 'pending').length}
                            valueStyle={{ color: '#faad14' }}
                            prefix={<ExclamationCircleOutlined />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 连接状态提示 */}
            {!isConnected && (
                <Alert
                    message="WebSocket连接已断开"
                    description="策略数据可能不是最新的，请检查网络连接"
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                />
            )}

            <Tabs defaultActiveKey="strategies">
                <TabPane tab="策略列表" key="strategies">
                    <Card title="策略管理" extra={
                        <Space>
                            <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
                                刷新
                            </Button>
                            <Tag color={isConnected ? 'green' : 'red'}>
                                {isConnected ? 'WebSocket已连接' : 'WebSocket连接已断开'}
                            </Tag>
                        </Space>
                    }>
                        <Table
                            columns={strategyColumns}
                            dataSource={strategyList}
                            rowKey="name"
                            size="small"
                            scroll={{ x: 1200 }}
                            pagination={false}
                            locale={{
                                emptyText: strategyList.length === 0 ? '暂无策略数据，请检查WebSocket连接和控制台日志' : '无数据'
                            }}
                        />
                    </Card>
                </TabPane>

                <TabPane tab="信号监控" key="signals">
                    <Card title="策略信号" extra={
                        <Space>
                            <Text>实时监控策略生成的交易信号</Text>
                        </Space>
                    }>
                        <Table
                            columns={signalColumns}
                            dataSource={signals}
                            rowKey="signal_id"
                            size="small"
                            scroll={{ x: 1400 }}
                            pagination={{ pageSize: 20 }}
                            locale={{
                                emptyText: '暂无信号数据'
                            }}
                        />
                    </Card>
                </TabPane>

                <TabPane tab="执行流程" key="execution">
                    <Card title="信号执行流程">
                        <Timeline
                            items={[
                                {
                                    color: 'blue',
                                    children: (
                                        <div>
                                            <Text strong>1. 信号生成</Text>
                                            <Paragraph>
                                                策略根据市场数据和Alpha函数计算生成交易信号
                                            </Paragraph>
                                        </div>
                                    ),
                                },
                                {
                                    color: 'orange',
                                    children: (
                                        <div>
                                            <Text strong>2. 信号验证</Text>
                                            <Paragraph>
                                                检查信号强度、风险控制、仓位限制等条件
                                            </Paragraph>
                                        </div>
                                    ),
                                },
                                {
                                    color: 'green',
                                    children: (
                                        <div>
                                            <Text strong>3. 订单生成</Text>
                                            <Paragraph>
                                                根据信号生成具体的交易订单，包括价格、数量等
                                            </Paragraph>
                                        </div>
                                    ),
                                },
                                {
                                    color: 'red',
                                    children: (
                                        <div>
                                            <Text strong>4. 订单执行</Text>
                                            <Paragraph>
                                                将订单发送到CTP交易系统进行实际执行
                                            </Paragraph>
                                        </div>
                                    ),
                                },
                                {
                                    color: 'purple',
                                    children: (
                                        <div>
                                            <Text strong>5. 结果反馈</Text>
                                            <Paragraph>
                                                接收交易结果，更新持仓和策略状态
                                            </Paragraph>
                                        </div>
                                    ),
                                },
                            ]}
                        />
                    </Card>
                </TabPane>
            </Tabs>

            {/* 信号详情抽屉 */}
            <Drawer
                title="信号详情"
                placement="right"
                onClose={() => setSignalDrawerVisible(false)}
                open={signalDrawerVisible}
                width={600}
            >
                {selectedSignal && (
                    <div>
                        <Descriptions title="基本信息" bordered size="small">
                            <Descriptions.Item label="信号ID" span={2}>
                                <Text code>{selectedSignal.signal_id}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="策略名称">
                                {selectedSignal.strategy_name}
                            </Descriptions.Item>
                            <Descriptions.Item label="交易品种">
                                <Tag color="blue">{selectedSignal.symbol}</Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="信号类型">
                                <Tag color={selectedSignal.signal_type === 'buy' ? 'red' : 'green'}>
                                    {selectedSignal.signal_type === 'buy' ? '做多' : '做空'}
                                </Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="信号强度">
                                <Progress
                                    percent={selectedSignal.signal_strength * 100}
                                    size="small"
                                    format={() => `${(selectedSignal.signal_strength * 100).toFixed(1)}%`}
                                />
                            </Descriptions.Item>
                            <Descriptions.Item label="Alpha值">
                                <Text style={{
                                    color: selectedSignal.alpha_value > 0 ? '#f5222d' : '#52c41a'
                                }}>
                                    {selectedSignal.alpha_value.toFixed(3)}
                                </Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="当前价格">
                                {selectedSignal.current_price.toFixed(2)}
                            </Descriptions.Item>
                            <Descriptions.Item label="目标价格">
                                {selectedSignal.target_price?.toFixed(2) || '--'}
                            </Descriptions.Item>
                            <Descriptions.Item label="止损价格">
                                {selectedSignal.stop_loss?.toFixed(2) || '--'}
                            </Descriptions.Item>
                            <Descriptions.Item label="建议仓位">
                                {selectedSignal.position_size} 手
                            </Descriptions.Item>
                            <Descriptions.Item label="生成时间" span={2}>
                                {new Date(selectedSignal.timestamp).toLocaleString()}
                            </Descriptions.Item>
                            <Descriptions.Item label="执行状态" span={2}>
                                <Badge
                                    status={selectedSignal.status === 'executed' ? 'success' :
                                        selectedSignal.status === 'pending' ? 'processing' : 'default'}
                                    text={selectedSignal.status === 'executed' ? '已执行' :
                                        selectedSignal.status === 'pending' ? '待执行' : '其他'}
                                />
                            </Descriptions.Item>
                        </Descriptions>

                        <Divider />

                        <div>
                            <Text strong>信号生成原因：</Text>
                            <Paragraph style={{ marginTop: 8 }}>
                                {selectedSignal.reason || '暂无详细说明'}
                            </Paragraph>
                        </div>

                        {selectedSignal.status === 'pending' && (
                            <div style={{ marginTop: 16 }}>
                                <Button
                                    type="primary"
                                    block
                                    onClick={() => executeSignal(selectedSignal)}
                                >
                                    立即执行信号
                                </Button>
                            </div>
                        )}

                        {selectedSignal.status === 'executed' && (
                            <Descriptions title="执行信息" bordered size="small" style={{ marginTop: 16 }}>
                                <Descriptions.Item label="执行价格">
                                    {selectedSignal.execution_price?.toFixed(2) || '--'}
                                </Descriptions.Item>
                                <Descriptions.Item label="执行时间">
                                    {selectedSignal.execution_time ?
                                        new Date(selectedSignal.execution_time).toLocaleString() : '--'}
                                </Descriptions.Item>
                            </Descriptions>
                        )}
                    </div>
                )}
            </Drawer>

            {/* 调试信息 */}
            <Card title="调试信息" style={{ marginTop: 16 }}>
                <div>
                    <p><strong>Redux Strategies数据:</strong> {JSON.stringify(Object.keys(strategies), null, 2)}</p>
                    <p><strong>策略列表数量:</strong> {strategyList.length}</p>
                    <p><strong>信号数量:</strong> {signals.length}</p>
                    <p><strong>最近系统日志:</strong></p>
                    <div style={{ maxHeight: 200, overflow: 'auto', fontSize: 12, fontFamily: 'monospace' }}>
                        {systemLogs.slice(-10).map((log, index) => (
                            <div key={index}>{log}</div>
                        ))}
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default StrategyPage; 