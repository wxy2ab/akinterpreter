import { Progress, Table, Tag, Typography } from 'antd';
import { ColumnType } from 'antd/lib/table';
import moment from 'moment';
import React, { useMemo } from 'react';
import { StrategyStatistics } from './StrategyTrackingPanel';

const { Text } = Typography;

interface StrategyStatisticsTableProps {
    statistics: StrategyStatistics[];
    loading: boolean;
}

export const StrategyStatisticsTable: React.FC<StrategyStatisticsTableProps> = ({
    statistics,
    loading
}) => {

    // 表格列定义
    const columns: ColumnType<StrategyStatistics>[] = useMemo(() => [
        {
            title: '策略名称',
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 250,
            fixed: 'left',
            ellipsis: true,
            render: (text: string) => (
                <Text strong style={{ color: '#1890ff' }}>
                    {text}
                </Text>
            )
        },
        {
            title: '信号总数',
            dataIndex: 'total_signals',
            key: 'total_signals',
            width: 120,
            sorter: (a, b) => a.total_signals - b.total_signals,
            render: (value: number) => (
                <Text>{value}</Text>
            )
        },
        {
            title: '成功信号',
            dataIndex: 'success_signals',
            key: 'success_signals',
            width: 120,
            sorter: (a, b) => a.success_signals - b.success_signals,
            render: (value: number) => (
                <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>
                    {value}
                </Text>
            )
        },
        {
            title: '成功率',
            dataIndex: 'success_rate',
            key: 'success_rate',
            width: 150,
            sorter: (a, b) => a.success_rate - b.success_rate,
            render: (value: number) => {
                const percentage = value.toFixed(1);
                const color = value >= 70 ? '#52c41a' : value >= 50 ? '#faad14' : '#ff4d4f';

                return (
                    <div>
                        <Progress
                            percent={value}
                            size="small"
                            strokeColor={color}
                            showInfo={false}
                            style={{ marginBottom: 4 }}
                        />
                        <Text style={{ color, fontWeight: 'bold' }}>
                            {percentage}%
                        </Text>
                    </div>
                );
            }
        },
        {
            title: '总盈亏',
            dataIndex: 'total_profit',
            key: 'total_profit',
            width: 150,
            sorter: (a, b) => a.total_profit - b.total_profit,
            render: (value: number) => {
                const color = value > 0 ? '#52c41a' : value < 0 ? '#ff4d4f' : '#000000';
                const prefix = value > 0 ? '+' : '';

                return (
                    <Text style={{ color, fontWeight: 'bold', fontSize: '14px' }}>
                        {prefix}¥{value.toFixed(2)}
                    </Text>
                );
            }
        },
        {
            title: '平均盈亏',
            dataIndex: 'avg_profit',
            key: 'avg_profit',
            width: 130,
            sorter: (a, b) => a.avg_profit - b.avg_profit,
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
            title: '最后信号时间',
            dataIndex: 'last_signal_time',
            key: 'last_signal_time',
            width: 150,
            sorter: (a, b) => {
                if (!a.last_signal_time) return 1;
                if (!b.last_signal_time) return -1;
                return moment(a.last_signal_time).unix() - moment(b.last_signal_time).unix();
            },
            render: (timestamp?: string) => {
                if (!timestamp) {
                    return <Text type="secondary">无信号</Text>;
                }

                const momentTime = moment(timestamp);
                const isToday = momentTime.isSame(moment(), 'day');
                const timeText = isToday
                    ? momentTime.format('HH:mm:ss')
                    : momentTime.format('MM-DD HH:mm');

                return (
                    <Text style={{ fontSize: '12px' }}>
                        {timeText}
                    </Text>
                );
            }
        },
        {
            title: '状态',
            key: 'status',
            width: 100,
            render: (_, record: StrategyStatistics) => {
                const isActive = record.last_signal_time &&
                    moment().diff(moment(record.last_signal_time), 'hours') < 24;

                return (
                    <Tag color={isActive ? 'green' : 'default'}>
                        {isActive ? '活跃' : '静默'}
                    </Tag>
                );
            }
        },
        {
            title: '等级',
            key: 'rating',
            width: 100,
            render: (_, record: StrategyStatistics) => {
                // 根据成功率和盈亏综合评级
                const { success_rate, total_profit } = record;
                let rating = 'C';
                let color = '#ff4d4f';

                if (success_rate >= 80 && total_profit > 1000) {
                    rating = 'S';
                    color = '#722ed1';
                } else if (success_rate >= 70 && total_profit > 500) {
                    rating = 'A';
                    color = '#52c41a';
                } else if (success_rate >= 60 && total_profit > 0) {
                    rating = 'B';
                    color = '#1890ff';
                } else if (success_rate >= 50) {
                    rating = 'C';
                    color = '#faad14';
                } else {
                    rating = 'D';
                    color = '#ff4d4f';
                }

                return (
                    <Tag color={color} style={{ fontWeight: 'bold' }}>
                        {rating}
                    </Tag>
                );
            }
        }
    ], []);

    // 计算总体统计
    const overallStats = useMemo(() => {
        const totalSignals = statistics.reduce((sum, s) => sum + s.total_signals, 0);
        const totalSuccessSignals = statistics.reduce((sum, s) => sum + s.success_signals, 0);
        const totalProfit = statistics.reduce((sum, s) => sum + s.total_profit, 0);
        const activeStrategies = statistics.filter(s =>
            s.last_signal_time && moment().diff(moment(s.last_signal_time), 'hours') < 24
        ).length;

        return {
            totalSignals,
            totalSuccessSignals,
            totalProfit,
            activeStrategies,
            overallSuccessRate: totalSignals > 0 ? (totalSuccessSignals / totalSignals * 100).toFixed(1) : '0.0',
            avgProfit: statistics.length > 0 ? (totalProfit / statistics.length).toFixed(2) : '0.00'
        };
    }, [statistics]);

    // 分页配置
    const pagination = useMemo(() => ({
        current: 1,
        pageSize: 20,
        total: statistics.length,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total: number, range: [number, number]) =>
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        pageSizeOptions: ['10', '20', '50'],
        size: 'small' as const
    }), [statistics.length]);

    return (
        <div className="strategy-statistics-table">
            <Table<StrategyStatistics>
                columns={columns}
                dataSource={statistics}
                loading={loading}
                pagination={pagination}
                rowKey="strategy_name"
                size="small"
                scroll={{ x: 1000, y: 400 }}
                bordered
                style={{ marginTop: 16 }}
                rowClassName={(record, index) => {
                    // 根据等级设置行样式
                    const { success_rate, total_profit } = record;
                    if (success_rate >= 80 && total_profit > 1000) {
                        return 'strategy-row-s';
                    } else if (success_rate >= 70 && total_profit > 500) {
                        return 'strategy-row-a';
                    } else if (success_rate >= 60 && total_profit > 0) {
                        return 'strategy-row-b';
                    } else if (success_rate >= 50) {
                        return 'strategy-row-c';
                    } else {
                        return 'strategy-row-d';
                    }
                }}
                summary={() => (
                    <Table.Summary fixed>
                        <Table.Summary.Row>
                            <Table.Summary.Cell index={0} colSpan={9}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Text strong>
                                        策略总数: {statistics.length}
                                    </Text>
                                    <div style={{ display: 'flex', gap: '24px' }}>
                                        <Text>
                                            活跃策略: <Text strong style={{ color: '#52c41a' }}>{overallStats.activeStrategies}</Text>
                                        </Text>
                                        <Text>
                                            总信号: <Text strong>{overallStats.totalSignals}</Text>
                                        </Text>
                                        <Text>
                                            成功信号: <Text strong style={{ color: '#52c41a' }}>{overallStats.totalSuccessSignals}</Text>
                                        </Text>
                                        <Text>
                                            整体成功率: <Text strong style={{ color: parseFloat(overallStats.overallSuccessRate) >= 50 ? '#52c41a' : '#ff4d4f' }}>
                                                {overallStats.overallSuccessRate}%
                                            </Text>
                                        </Text>
                                        <Text>
                                            总盈亏: <Text strong style={{ color: overallStats.totalProfit >= 0 ? '#52c41a' : '#ff4d4f' }}>
                                                {overallStats.totalProfit >= 0 ? '+' : ''}¥{overallStats.totalProfit.toFixed(2)}
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
        .strategy-statistics-table :global(.strategy-row-s) {
          background-color: #f9f0ff !important;
        }
        
        .strategy-statistics-table :global(.strategy-row-a) {
          background-color: #f6ffed !important;
        }
        
        .strategy-statistics-table :global(.strategy-row-b) {
          background-color: #e6f7ff !important;
        }
        
        .strategy-statistics-table :global(.strategy-row-c) {
          background-color: #fffbe6 !important;
        }
        
        .strategy-statistics-table :global(.strategy-row-d) {
          background-color: #fff2f0 !important;
        }
        
        .strategy-statistics-table :global(.ant-table-tbody) > :global(.ant-table-row):hover > :global(.ant-table-cell) {
          background: #e6f7ff !important;
        }
      `}</style>
        </div>
    );
}; 