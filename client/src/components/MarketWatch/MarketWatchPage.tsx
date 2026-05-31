import {
    ReloadOutlined,
    SearchOutlined,
    SettingOutlined,
    SyncOutlined
} from '@ant-design/icons';
import {
    Button,
    Card,
    Col,
    Input,
    Row,
    Select,
    Space,
    Statistic,
    Table,
    Tag,
    Typography
} from 'antd';
import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';

import { useWebSocket } from '../../context/WebSocketContext';
import { RootState } from '../../store/store';

const { Title, Text } = Typography;
const { Option } = Select;

// 合约信息接口
interface ContractInfo {
    symbol: string;
    name: string;
    exchange: string;
    product_class: string;
    volume_multiple: number;
    price_tick: number;
    max_limit_order_volume: number;
    min_limit_order_volume: number;
    max_market_order_volume: number;
    min_market_order_volume: number;
    underlying_symbol?: string;
    strike_price?: number;
    options_type?: string;
    underlying_multiple?: number;
    create_date?: string;
    open_date?: string;
    expire_date?: string;
    start_deliver_date?: string;
    end_deliver_date?: string;
    is_trading?: boolean;
    position_type?: string;
    position_date_type?: string;
}

// 行情数据接口
interface MarketData {
    symbol: string;
    exchange: string;
    last_price: number;
    volume: number;
    turnover: number;
    open_interest: number;
    bid_price_1: number;
    bid_volume_1: number;
    ask_price_1: number;
    ask_volume_1: number;
    highest_price: number;
    lowest_price: number;
    open_price: number;
    close_price: number;
    upper_limit_price: number;
    lower_limit_price: number;
    pre_close_price: number;
    pre_settlement_price: number;
    settlement_price: number;
    pre_open_interest: number;
    update_time: string;
    update_millisec: number;
    trading_day: string;
    action_day: string;
    change: number;
    change_percent: number;
}

const MarketWatchPage: React.FC = () => {
    const [searchText, setSearchText] = useState('');
    const [selectedExchange, setSelectedExchange] = useState<string>('');
    const [loading, setLoading] = useState(false);

    const { isConnected, sendMessage } = useWebSocket();

    // 从Redux store获取行情数据
    const marketData = useSelector((state: RootState) => state.market.ticks);
    const systemLogs = useSelector((state: RootState) => state.system.logs);

    console.log('MarketWatchPage - Redux market data:', marketData);
    console.log('MarketWatchPage - WebSocket connected:', isConnected);

    // 智能推测合约代码的函数
    const guessSymbolFromPrice = (price: number): string => {
        if (price >= 8000 && price <= 10000) {
            return 'rb2501'; // 螺纹钢
        } else if (price >= 3000 && price <= 5000) {
            return 'hc2501'; // 热卷
        } else if (price >= 800 && price <= 1200) {
            return 'i2501'; // 铁矿石
        } else if (price >= 2000 && price <= 2500) {
            return 'j2501'; // 焦炭
        } else if (price >= 1500 && price <= 2000) {
            return 'jm2501'; // 焦煤
        }
        return 'unknown';
    };

    // 转换Redux数据为表格数据
    const tableData: MarketData[] = Object.entries(marketData).map(([symbol, tick]) => {
        // 如果symbol为空，尝试根据价格推测
        const actualSymbol = symbol || guessSymbolFromPrice(tick.last_price) || 'unknown';

        return {
            symbol: actualSymbol,
            exchange: tick.exchange || 'SHFE',
            last_price: tick.last_price || 0,
            volume: tick.volume || 0,
            turnover: tick.turnover || 0,
            open_interest: tick.open_interest || 0,
            bid_price_1: tick.bid_price_1 || 0,
            bid_volume_1: tick.bid_volume_1 || 0,
            ask_price_1: tick.ask_price_1 || 0,
            ask_volume_1: tick.ask_volume_1 || 0,
            highest_price: tick.highest_price || 0,
            lowest_price: tick.lowest_price || 0,
            open_price: tick.open_price || 0,
            close_price: tick.close_price || 0,
            upper_limit_price: tick.upper_limit_price || 0,
            lower_limit_price: tick.lower_limit_price || 0,
            pre_close_price: tick.pre_close_price || 0,
            pre_settlement_price: tick.pre_settlement_price || 0,
            settlement_price: tick.settlement_price || 0,
            pre_open_interest: tick.pre_open_interest || 0,
            update_time: tick.update_time || '',
            update_millisec: tick.update_millisec || 0,
            trading_day: tick.trading_day || '',
            action_day: tick.action_day || '',
            change: tick.change || 0,
            change_percent: tick.change_percent || 0
        };
    });

    // 过滤数据
    const filteredData = tableData.filter(item => {
        const matchesSearch = !searchText ||
            item.symbol.toLowerCase().includes(searchText.toLowerCase());
        const matchesExchange = !selectedExchange || item.exchange === selectedExchange;
        return matchesSearch && matchesExchange;
    });

    // 订阅行情数据
    useEffect(() => {
        if (isConnected) {
            console.log('MarketWatch: WebSocket已连接，订阅行情数据');
            sendMessage({
                type: 'subscribe',
                event_types: ['market_tick', 'tick_update']
            });

            // 请求最新行情数据
            sendMessage({
                type: 'get_latest_data',
                event_types: ['market_tick']
            });
        }
    }, [isConnected, sendMessage]);

    // 表格列定义
    const columns = [
        {
            title: '合约代码',
            dataIndex: 'symbol',
            key: 'symbol',
            width: 120,
            render: (symbol: string) => (
                <Text strong style={{ fontFamily: 'monospace' }}>
                    {symbol}
                </Text>
            ),
        },
        {
            title: '交易所',
            dataIndex: 'exchange',
            key: 'exchange',
            width: 80,
            render: (exchange: string) => (
                <Tag color="blue">{exchange}</Tag>
            ),
        },
        {
            title: '最新价',
            dataIndex: 'last_price',
            key: 'last_price',
            width: 100,
            render: (price: number, record: MarketData) => (
                <Text strong style={{
                    color: record.change > 0 ? '#f5222d' : record.change < 0 ? '#52c41a' : '#666',
                    fontFamily: 'monospace'
                }}>
                    {price.toFixed(2)}
                </Text>
            ),
        },
        {
            title: '涨跌',
            dataIndex: 'change',
            key: 'change',
            width: 80,
            render: (change: number) => (
                <Text style={{
                    color: change > 0 ? '#f5222d' : change < 0 ? '#52c41a' : '#666',
                    fontFamily: 'monospace'
                }}>
                    {change > 0 ? '+' : ''}{change.toFixed(2)}
                </Text>
            ),
        },
        {
            title: '涨跌幅',
            dataIndex: 'change_percent',
            key: 'change_percent',
            width: 100,
            render: (percent: number) => (
                <Text style={{
                    color: percent > 0 ? '#f5222d' : percent < 0 ? '#52c41a' : '#666',
                    fontFamily: 'monospace'
                }}>
                    {percent > 0 ? '+' : ''}{(percent * 100).toFixed(2)}%
                </Text>
            ),
        },
        {
            title: '成交量',
            dataIndex: 'volume',
            key: 'volume',
            width: 100,
            render: (volume: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {volume.toLocaleString()}
                </Text>
            ),
        },
        {
            title: '持仓量',
            dataIndex: 'open_interest',
            key: 'open_interest',
            width: 100,
            render: (oi: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {oi.toLocaleString()}
                </Text>
            ),
        },
        {
            title: '买一价',
            dataIndex: 'bid_price_1',
            key: 'bid_price_1',
            width: 100,
            render: (price: number) => (
                <Text style={{ color: '#52c41a', fontFamily: 'monospace' }}>
                    {price.toFixed(2)}
                </Text>
            ),
        },
        {
            title: '买一量',
            dataIndex: 'bid_volume_1',
            key: 'bid_volume_1',
            width: 80,
            render: (volume: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {volume}
                </Text>
            ),
        },
        {
            title: '卖一价',
            dataIndex: 'ask_price_1',
            key: 'ask_price_1',
            width: 100,
            render: (price: number) => (
                <Text style={{ color: '#f5222d', fontFamily: 'monospace' }}>
                    {price.toFixed(2)}
                </Text>
            ),
        },
        {
            title: '卖一量',
            dataIndex: 'ask_volume_1',
            key: 'ask_volume_1',
            width: 80,
            render: (volume: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {volume}
                </Text>
            ),
        },
        {
            title: '更新时间',
            dataIndex: 'update_time',
            key: 'update_time',
            width: 120,
            render: (time: string) => (
                <Text style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                    {time}
                </Text>
            ),
        },
    ];

    const handleRefresh = () => {
        setLoading(true);
        if (isConnected) {
            sendMessage({
                type: 'get_latest_data',
                event_types: ['market_tick']
            });
        }
        setTimeout(() => setLoading(false), 1000);
    };

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>实时行情</Title>

            {/* 统计信息 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="监控合约数"
                            value={tableData.length}
                            prefix={<SyncOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="上涨合约"
                            value={tableData.filter(item => item.change > 0).length}
                            valueStyle={{ color: '#f5222d' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="下跌合约"
                            value={tableData.filter(item => item.change < 0).length}
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="平盘合约"
                            value={tableData.filter(item => item.change === 0).length}
                            valueStyle={{ color: '#666' }}
                        />
                    </Card>
                </Col>
            </Row>

            <Card
                title="行情数据"
                extra={
                    <Space>
                        <Input
                            placeholder="搜索合约代码"
                            prefix={<SearchOutlined />}
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            style={{ width: 200 }}
                        />
                        <Select
                            placeholder="选择交易所"
                            style={{ width: 120 }}
                            value={selectedExchange}
                            onChange={setSelectedExchange}
                            allowClear
                        >
                            <Option value="SHFE">上期所</Option>
                            <Option value="DCE">大商所</Option>
                            <Option value="CZCE">郑商所</Option>
                            <Option value="CFFEX">中金所</Option>
                            <Option value="INE">上能所</Option>
                        </Select>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={handleRefresh}
                            loading={loading}
                        >
                            刷新
                        </Button>
                        <Button icon={<SettingOutlined />}>
                            设置
                        </Button>
                        <Tag color={isConnected ? 'green' : 'red'}>
                            {isConnected ? 'WebSocket已连接' : 'WebSocket连接已断开'}
                        </Tag>
                    </Space>
                }
            >
                <Table
                    columns={columns}
                    dataSource={filteredData}
                    rowKey="symbol"
                    size="small"
                    scroll={{ x: 1200, y: 600 }}
                    pagination={{
                        pageSize: 50,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 条数据`,
                    }}
                    locale={{
                        emptyText: tableData.length === 0 ? '暂无行情数据，请检查WebSocket连接和控制台日志' : '无匹配数据'
                    }}
                />
            </Card>

            {/* 调试信息 */}
            <Card title="调试信息" style={{ marginTop: 16 }}>
                <div>
                    <p><strong>Redux Market数据:</strong> {JSON.stringify(Object.keys(marketData), null, 2)}</p>
                    <p><strong>表格数据数量:</strong> {tableData.length}</p>
                    <p><strong>过滤后数据数量:</strong> {filteredData.length}</p>
                    <p><strong>WebSocket连接状态:</strong> {isConnected ? '已连接' : '未连接'}</p>
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

export default MarketWatchPage;