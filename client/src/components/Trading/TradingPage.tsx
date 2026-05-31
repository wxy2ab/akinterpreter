import {
    BankOutlined,
    DollarOutlined,
    ExclamationCircleOutlined,
    ReloadOutlined,
    ShoppingCartOutlined,
    TransactionOutlined
} from '@ant-design/icons';
import {
    Button,
    Card,
    Col,
    Form,
    Modal,
    Row,
    Select,
    Space,
    Statistic,
    Table,
    Tabs,
    Tag,
    Typography,
    message
} from 'antd';
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useWebSocket } from '../../context/WebSocketContext';
import { RootState } from '../../store/store';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const { confirm } = Modal;

// 使用Redux store中的类型定义
interface Position {
    symbol: string;
    direction: string;
    position: number;
    position_cost: number;
    open_cost: number;
    position_profit: number;
    close_profit: number;
    margin: number;
    exchange_margin: number;
    pre_settlement_price: number;
    settlement_price: number;
    trading_day: string;
}

interface Order {
    order_id: string;
    symbol: string;
    direction: string;
    offset_flag: string;
    price: number;
    volume: number;
    volume_traded: number;
    volume_total: number;
    status: string;
    status_msg: string;
    insert_time: string;
    update_time: string;
    front_id: number;
    session_id: number;
}

interface Trade {
    trade_id: string;
    order_id: string;
    symbol: string;
    direction: string;
    offset_flag: string;
    price: number;
    volume: number;
    trade_time: string;
    trade_date: string;
    commission: number;
}

const TradingPage: React.FC = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);

    const dispatch = useDispatch();
    const { isConnected, sendMessage } = useWebSocket();

    // 从Redux store获取交易数据
    const positions = useSelector((state: RootState) => state.trading.positions);
    const orders = useSelector((state: RootState) => state.trading.orders);
    const trades = useSelector((state: RootState) => state.trading.trades);
    const accountInfo = useSelector((state: RootState) => state.account);
    const systemLogs = useSelector((state: RootState) => state.system.logs);

    console.log('TradingPage - Redux positions:', positions);
    console.log('TradingPage - Redux orders:', orders);
    console.log('TradingPage - Redux trades:', trades);
    console.log('TradingPage - Redux account:', accountInfo);

    // 转换Redux数据为数组格式
    const positionList: Position[] = Object.values(positions);
    const orderList: Order[] = Object.values(orders);
    const tradeList: Trade[] = Object.values(trades);

    console.log('TradingPage - Position list:', positionList);
    console.log('TradingPage - Order list:', orderList);
    console.log('TradingPage - Trade list:', tradeList);

    // 订阅交易数据
    useEffect(() => {
        if (isConnected) {
            console.log('TradingPage: WebSocket已连接，订阅交易数据');
            sendMessage({
                type: 'subscribe',
                event_types: ['position_update', 'order_update', 'trade_update', 'account_update']
            });

            // 请求最新数据
            sendMessage({
                type: 'get_latest_data',
                event_types: ['position_update', 'order_update', 'trade_update', 'account_update']
            });
        }
    }, [isConnected, sendMessage]);

    // 提交订单
    const handleSubmitOrder = async (values: any) => {
        setLoading(true);
        try {
            const response = await fetch('/api/trading/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: values.symbol,
                    direction: values.direction,
                    offset: values.offset,
                    price: values.price,
                    volume: values.volume,
                    order_type: values.order_type || 'limit'
                }),
            });

            const result = await response.json();

            if (result.success) {
                message.success('订单提交成功');
                form.resetFields();
            } else {
                message.error(`订单提交失败: ${result.message}`);
            }
        } catch (error) {
            message.error('订单提交失败，请检查网络连接');
        } finally {
            setLoading(false);
        }
    };

    // 撤销订单
    const handleCancelOrder = (orderId: string) => {
        confirm({
            title: '确认撤销订单',
            icon: <ExclamationCircleOutlined />,
            content: `确定要撤销订单 ${orderId} 吗？`,
            onOk: async () => {
                try {
                    const response = await fetch(`/api/trading/orders/${orderId}`, {
                        method: 'DELETE',
                    });

                    const result = await response.json();

                    if (result.success) {
                        message.success('订单撤销成功');
                    } else {
                        message.error(`订单撤销失败: ${result.message}`);
                    }
                } catch (error) {
                    message.error('订单撤销失败，请检查网络连接');
                }
            },
        });
    };

    // 平仓
    const handleClosePosition = (position: Position) => {
        const oppositeDirection = position.direction === 'buy' ? 'sell' : 'buy';

        form.setFieldsValue({
            symbol: position.symbol,
            direction: oppositeDirection,
            offset: 'close',
            volume: position.position,
            order_type: 'market'
        });

        message.info(`已自动填入平仓参数，请确认后提交`);
    };

    // 持仓表格列
    const positionColumns = [
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
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            width: 80,
            render: (direction: string) => (
                <Tag color={direction === 'long' ? 'red' : 'green'}>
                    {direction === 'long' ? '多头' : '空头'}
                </Tag>
            ),
        },
        {
            title: '持仓量',
            dataIndex: 'position',
            key: 'position',
            width: 100,
            render: (position: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {position || 0}
                </Text>
            ),
        },
        {
            title: '开仓均价',
            dataIndex: 'avg_open_price',
            key: 'avg_open_price',
            width: 120,
            render: (price: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {price ? price.toFixed(2) : '--'}
                </Text>
            ),
        },
        {
            title: '当前价格',
            dataIndex: 'last_price',
            key: 'last_price',
            width: 120,
            render: (price: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {price ? price.toFixed(2) : '--'}
                </Text>
            ),
        },
        {
            title: '浮动盈亏',
            dataIndex: 'unrealized_pnl',
            key: 'unrealized_pnl',
            width: 120,
            render: (pnl: number) => (
                <Text style={{
                    color: pnl > 0 ? '#f5222d' : pnl < 0 ? '#52c41a' : '#666',
                    fontFamily: 'monospace'
                }}>
                    {pnl ? pnl.toFixed(2) : '0.00'}
                </Text>
            ),
        },
        {
            title: '保证金',
            dataIndex: 'margin',
            key: 'margin',
            width: 120,
            render: (margin: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {margin ? margin.toFixed(2) : '--'}
                </Text>
            ),
        },
    ];

    // 订单表格列
    const orderColumns = [
        {
            title: '订单号',
            dataIndex: 'order_id',
            key: 'order_id',
            width: 150,
            render: (orderId: string) => (
                <Text code style={{ fontSize: '12px' }}>
                    {orderId ? orderId.slice(-8) : '--'}
                </Text>
            ),
        },
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
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            width: 80,
            render: (direction: string) => (
                <Tag color={direction === 'buy' ? 'red' : 'green'}>
                    {direction === 'buy' ? '买入' : '卖出'}
                </Tag>
            ),
        },
        {
            title: '开平',
            dataIndex: 'offset_flag',
            key: 'offset_flag',
            width: 80,
            render: (offset: string) => (
                <Tag color="blue">
                    {offset === 'open' ? '开仓' : offset === 'close' ? '平仓' : offset || '--'}
                </Tag>
            ),
        },
        {
            title: '数量',
            dataIndex: 'volume',
            key: 'volume',
            width: 80,
            render: (volume: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {volume || 0}
                </Text>
            ),
        },
        {
            title: '价格',
            dataIndex: 'price',
            key: 'price',
            width: 100,
            render: (price: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {price ? price.toFixed(2) : '--'}
                </Text>
            ),
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => {
                const statusMap: Record<string, { color: string; text: string }> = {
                    'submitted': { color: 'processing', text: '已提交' },
                    'filled': { color: 'success', text: '已成交' },
                    'cancelled': { color: 'default', text: '已撤销' },
                    'rejected': { color: 'error', text: '已拒绝' },
                    'partial_filled': { color: 'warning', text: '部分成交' }
                };
                const config = statusMap[status] || { color: 'default', text: status || '未知' };
                return <Tag color={config.color}>{config.text}</Tag>;
            },
        },
        {
            title: '时间',
            dataIndex: 'insert_time',
            key: 'insert_time',
            width: 150,
            render: (time: string) => (
                <Text style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                    {time || '--'}
                </Text>
            ),
        },
    ];

    // 成交表格列
    const tradeColumns = [
        {
            title: '成交号',
            dataIndex: 'trade_id',
            key: 'trade_id',
            width: 150,
            render: (tradeId: string) => (
                <Text code style={{ fontSize: '12px' }}>
                    {tradeId ? tradeId.slice(-8) : '--'}
                </Text>
            ),
        },
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
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            width: 80,
            render: (direction: string) => (
                <Tag color={direction === 'buy' ? 'red' : 'green'}>
                    {direction === 'buy' ? '买入' : '卖出'}
                </Tag>
            ),
        },
        {
            title: '数量',
            dataIndex: 'volume',
            key: 'volume',
            width: 80,
            render: (volume: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {volume || 0}
                </Text>
            ),
        },
        {
            title: '成交价',
            dataIndex: 'price',
            key: 'price',
            width: 100,
            render: (price: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {price ? price.toFixed(2) : '--'}
                </Text>
            ),
        },
        {
            title: '手续费',
            dataIndex: 'commission',
            key: 'commission',
            width: 100,
            render: (commission: number) => (
                <Text style={{ fontFamily: 'monospace' }}>
                    {commission ? commission.toFixed(2) : '--'}
                </Text>
            ),
        },
        {
            title: '成交时间',
            dataIndex: 'trade_date',
            key: 'trade_date',
            width: 150,
            render: (time: string) => (
                <Text style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                    {time || '--'}
                </Text>
            ),
        },
    ];

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>交易管理</Title>

            {/* 连接状态和数据统计 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="账户余额"
                            value={accountInfo.balance || 0}
                            precision={2}
                            valueStyle={{ color: '#3f8600' }}
                            prefix={<DollarOutlined />}
                            suffix="元"
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="可用资金"
                            value={accountInfo.available || 0}
                            precision={2}
                            valueStyle={{ color: '#1890ff' }}
                            prefix={<BankOutlined />}
                            suffix="元"
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="保证金占用"
                            value={accountInfo.margin || 0}
                            precision={2}
                            valueStyle={{ color: '#faad14' }}
                            prefix={<ExclamationCircleOutlined />}
                            suffix="元"
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="浮动盈亏"
                            value={accountInfo.unrealized_pnl || 0}
                            precision={2}
                            valueStyle={{ color: (accountInfo.unrealized_pnl || 0) >= 0 ? '#f5222d' : '#52c41a' }}
                            prefix={<TransactionOutlined />}
                            suffix="元"
                        />
                    </Card>
                </Col>
            </Row>

            {/* 数据统计 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="持仓数量"
                            value={positionList.length}
                            prefix={<ShoppingCartOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="活跃订单"
                            value={orderList.filter(order =>
                                order.status === 'submitted' || order.status === 'partial_filled'
                            ).length}
                            valueStyle={{ color: '#faad14' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="今日成交"
                            value={tradeList.length}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="WebSocket状态"
                            value={isConnected ? "已连接" : "未连接"}
                            valueStyle={{ color: isConnected ? '#52c41a' : '#f5222d' }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 持仓表格 */}
            <Card
                title="持仓管理"
                style={{ marginBottom: 16 }}
                extra={
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
                            刷新
                        </Button>
                        <Tag color={isConnected ? 'green' : 'red'}>
                            {isConnected ? 'WebSocket已连接' : 'WebSocket连接已断开'}
                        </Tag>
                    </Space>
                }
            >
                <Table
                    columns={positionColumns}
                    dataSource={positionList}
                    size="small"
                    scroll={{ x: 800 }}
                    pagination={false}
                    locale={{
                        emptyText: positionList.length === 0 ? '暂无持仓数据' : '无数据'
                    }}
                />
            </Card>

            {/* 订单表格 */}
            <Card title="订单管理" style={{ marginBottom: 16 }}>
                <Table
                    columns={orderColumns}
                    dataSource={orderList}
                    size="small"
                    scroll={{ x: 1000 }}
                    pagination={{ pageSize: 10 }}
                    locale={{
                        emptyText: orderList.length === 0 ? '暂无订单数据' : '无数据'
                    }}
                />
            </Card>

            {/* 成交表格 */}
            <Card title="成交记录" style={{ marginBottom: 16 }}>
                <Table
                    columns={tradeColumns}
                    dataSource={tradeList}
                    size="small"
                    scroll={{ x: 1000 }}
                    pagination={{ pageSize: 10 }}
                    locale={{
                        emptyText: tradeList.length === 0 ? '暂无成交数据' : '无数据'
                    }}
                />
            </Card>

            {/* 调试信息 */}
            <Card title="调试信息">
                <div>
                    <p><strong>Redux Positions数据:</strong> {JSON.stringify(Object.keys(positions), null, 2)}</p>
                    <p><strong>Redux Orders数据:</strong> {JSON.stringify(Object.keys(orders), null, 2)}</p>
                    <p><strong>Redux Trades数据:</strong> {JSON.stringify(Object.keys(trades), null, 2)}</p>
                    <p><strong>持仓数量:</strong> {positionList.length}</p>
                    <p><strong>订单数量:</strong> {orderList.length}</p>
                    <p><strong>成交数量:</strong> {tradeList.length}</p>
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

export default TradingPage; 