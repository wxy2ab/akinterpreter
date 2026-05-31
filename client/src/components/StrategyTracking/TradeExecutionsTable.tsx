import { Table, Tag, Tooltip, Typography } from 'antd';
import { ColumnType } from 'antd/lib/table';
import moment from 'moment';
import React, { useMemo } from 'react';
import { FilterParams, TradeExecution } from './StrategyTrackingPanel';

const { Text } = Typography;

interface TradeExecutionsTableProps {
    trades: TradeExecution[];
    loading: boolean;
    filterParams: FilterParams;
}

export const TradeExecutionsTable: React.FC<TradeExecutionsTableProps> = ({
    trades,
    loading,
    filterParams
}) => {

    // 获取执行状态颜色
    const getStatusColor = (status: string): string => {
        switch (status.toLowerCase()) {
            case 'submitted':
                return 'processing';
            case 'partiallyfilled':
                return 'warning';
            case 'filled':
                return 'success';
            case 'rejected':
                return 'error';
            case 'cancelled':
                return 'default';
            default:
                return 'default';
        }
    };

    // 获取方向颜色
    const getDirectionColor = (direction: string): string => {
        const dir = direction.toLowerCase();
        if (['buy', 'open_long', '买入'].includes(dir)) {
            return 'green';
        } else if (['sell', 'open_short', '卖出'].includes(dir)) {
            return 'red';
        } else if (['close', 'close_long', 'close_short', '平仓'].includes(dir)) {
            return 'orange';
        } else {
            return 'blue';
        }
    };

    // 表格列定义
    const columns: ColumnType<TradeExecution>[] = useMemo(() => [
        {
            title: '时间',
            dataIndex: 'timestamp',
            key: 'timestamp',
            width: 120,
            fixed: 'left',
            sorter: (a, b) => moment(a.timestamp).unix() - moment(b.timestamp).unix(),
            defaultSortOrder: 'descend',
            render: (timestamp: string) => (
                <Tooltip title={moment(timestamp).format('YYYY-MM-DD HH:mm:ss')}>
                    <Text style={{ fontSize: '12px' }}>
                        {moment(timestamp).format('HH:mm:ss')}
                    </Text>
                </Tooltip>
            )
        },
        {
            title: '策略名称',
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 180,
            ellipsis: true,
            render: (text: string) => (
                <Tooltip title={text}>
                    <Text strong style={{ color: '#1890ff' }}>
                        {text}
                    </Text>
                </Tooltip>
            )
        },
        {
            title: '合约',
            dataIndex: 'symbol',
            key: 'symbol',
            width: 100,
            render: (text: string) => (
                <Tag color="blue">{text}</Tag>
            )
        },
        {
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            width: 100,
            render: (text: string) => (
                <Tag color={getDirectionColor(text)}>
                    {text}
                </Tag>
            )
        },
        {
            title: '价格',
            dataIndex: 'price',
            key: 'price',
            width: 100,
            sorter: (a, b) => a.price - b.price,
            render: (value: number) => (
                <Text>{value.toFixed(2)}</Text>
            )
        },
        {
            title: '数量',
            dataIndex: 'quantity',
            key: 'quantity',
            width: 80,
            sorter: (a, b) => a.quantity - b.quantity,
            render: (value: number) => (
                <Text>{value}</Text>
            )
        },
        {
            title: '成交量',
            dataIndex: 'filled_quantity',
            key: 'filled_quantity',
            width: 80,
            sorter: (a, b) => a.filled_quantity - b.filled_quantity,
            render: (value: number, record: TradeExecution) => {
                const fillRate = record.quantity > 0 ? (value / record.quantity * 100).toFixed(1) : '0.0';
                const color = value === record.quantity ? '#52c41a' : value > 0 ? '#faad14' : '#ff4d4f';

                return (
                    <Tooltip title={`成交率: ${fillRate}%`}>
                        <Text style={{ color }}>
                            {value}
                        </Text>
                    </Tooltip>
                );
            }
        },
        {
            title: '执行状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (text: string) => (
                <Tag color={getStatusColor(text)}>
                    {text}
                </Tag>
            )
        },
        {
            title: '盈亏',
            dataIndex: 'pnl',
            key: 'pnl',
            width: 100,
            sorter: (a, b) => a.pnl - b.pnl,
            render: (value: number) => {
                const color = value > 0 ? '#52c41a' : value < 0 ? '#ff4d4f' : '#000000';
                const prefix = value > 0 ? '+' : '';

                return (
                    <Text style={{ color, fontWeight: 'bold' }}>
                        {prefix}¥{value.toFixed(2)}
                    </Text>
                );
            }
        },
        {
            title: '备注',
            dataIndex: 'notes',
            key: 'notes',
            width: 150,
            ellipsis: true,
            render: (text: string) => (
                <Tooltip title={text}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                        {text || '-'}
                    </Text>
                </Tooltip>
            )
        },
        {
            title: '订单ID',
            dataIndex: 'order_id',
            key: 'order_id',
            width: 120,
            ellipsis: true,
            render: (text: string) => (
                <Tooltip title={text}>
                    <Text code style={{ fontSize: '11px' }}>
                        {text || '-'}
                    </Text>
                </Tooltip>
            )
        }
    ], []);

    // 计算统计信息
    const statistics = useMemo(() => {
        const totalTrades = trades.length;
        const filledTrades = trades.filter(t => t.status === 'Filled').length;
        const totalPnl = trades.reduce((sum, t) => sum + t.pnl, 0);
        const profitTrades = trades.filter(t => t.pnl > 0).length;
        const lossTrades = trades.filter(t => t.pnl < 0).length;

        return {
            totalTrades,
            filledTrades,
            totalPnl,
            profitTrades,
            lossTrades,
            fillRate: totalTrades > 0 ? (filledTrades / totalTrades * 100).toFixed(1) : '0.0',
            winRate: (profitTrades + lossTrades) > 0 ? (profitTrades / (profitTrades + lossTrades) * 100).toFixed(1) : '0.0'
        };
    }, [trades]);

    // 分页配置
    const pagination = useMemo(() => ({
        current: 1,
        pageSize: 50,
        total: trades.length,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total: number, range: [number, number]) =>
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        pageSizeOptions: ['20', '50', '100', '200'],
        size: 'small' as const
    }), [trades.length]);

    return (
        <div className="trade-executions-table">
            <Table<TradeExecution>
                columns={columns}
                dataSource={trades}
                loading={loading}
                pagination={pagination}
                rowKey="trade_id"
                size="small"
                scroll={{ x: 1200, y: 400 }}
                bordered
                style={{ marginTop: 16 }}
                rowClassName={(record, index) => {
                    // 根据盈亏设置行样式
                    if (record.pnl > 0) {
                        return 'trade-row-profit';
                    } else if (record.pnl < 0) {
                        return 'trade-row-loss';
                    } else {
                        return '';
                    }
                }}
                summary={() => (
                    <Table.Summary fixed>
                        <Table.Summary.Row>
                            <Table.Summary.Cell index={0} colSpan={11}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Text strong>
                                        总计: {statistics.totalTrades} 笔交易
                                    </Text>
                                    <div style={{ display: 'flex', gap: '24px' }}>
                                        <Text>
                                            成交: <Text strong style={{ color: '#52c41a' }}>{statistics.filledTrades}</Text>
                                            ({statistics.fillRate}%)
                                        </Text>
                                        <Text>
                                            盈利: <Text strong style={{ color: '#52c41a' }}>{statistics.profitTrades}</Text>
                                        </Text>
                                        <Text>
                                            亏损: <Text strong style={{ color: '#ff4d4f' }}>{statistics.lossTrades}</Text>
                                        </Text>
                                        <Text>
                                            胜率: <Text strong style={{ color: parseFloat(statistics.winRate) >= 50 ? '#52c41a' : '#ff4d4f' }}>
                                                {statistics.winRate}%
                                            </Text>
                                        </Text>
                                        <Text>
                                            总盈亏: <Text strong style={{ color: statistics.totalPnl >= 0 ? '#52c41a' : '#ff4d4f' }}>
                                                {statistics.totalPnl >= 0 ? '+' : ''}¥{statistics.totalPnl.toFixed(2)}
                                            </Text>
                                        </Text>
                                    </div>
                                </div>
                            </Table.Summary.Cell>
                        </Table.Summary.Row>
                    </Table.Summary>
                )}
            />

            <style>{`
        .trade-executions-table :global(.trade-row-profit) {
          background-color: #f6ffed !important;
        }
        
        .trade-executions-table :global(.trade-row-loss) {
          background-color: #fff2f0 !important;
        }
        
        .trade-executions-table :global(.ant-table-tbody) > :global(.ant-table-row):hover > :global(.ant-table-cell) {
          background: #e6f7ff !important;
        }
      `}</style>
        </div>
    );
}; 