import { Table, Tag, Tooltip, Typography } from 'antd';
import { ColumnType } from 'antd/lib/table';
import moment from 'moment';
import React, { useMemo } from 'react';
import { FilterParams, StrategySignal } from './StrategyTrackingPanel';

const { Text } = Typography;

interface StrategySignalsTableProps {
    signals: StrategySignal[];
    loading: boolean;
    filterParams: FilterParams;
}

export const StrategySignalsTable: React.FC<StrategySignalsTableProps> = ({
    signals,
    loading,
    filterParams
}) => {

    // 格式化Alpha值显示
    const formatAlphaValue = (alphaValue: number): string => {
        if (alphaValue <= -900) {
            return `E${Math.abs(alphaValue)}`;
        } else if (Math.abs(alphaValue) < 0.001) {
            return "0.000";
        } else {
            return alphaValue.toFixed(3);
        }
    };

    // 获取Alpha值含义
    const getAlphaMeaning = (alphaValue: number): string => {
        if (alphaValue <= -905) {
            return "数据不足或准备失败";
        } else if (alphaValue <= -904) {
            return "不在交易时间窗口";
        } else if (alphaValue <= -903) {
            return "集合竞价时间";
        } else if (alphaValue <= -902) {
            return "策略被禁用";
        } else if (alphaValue <= -901) {
            return "配置未找到";
        } else if (alphaValue <= -900) {
            return "其他系统错误";
        } else {
            return `正常Alpha信号值: ${alphaValue.toFixed(4)}`;
        }
    };

    // 获取信号类型颜色
    const getSignalTypeColor = (signalType: string): string => {
        const type = signalType.toLowerCase();
        if (['buy', 'open_long', '买入'].includes(type)) {
            return 'green';
        } else if (['sell', 'open_short', '卖出'].includes(type)) {
            return 'red';
        } else if (['close', 'close_long', 'close_short', '平仓'].includes(type)) {
            return 'orange';
        } else if (['hold', '持有'].includes(type)) {
            return 'default';
        } else if (['position', '仓位调整'].includes(type)) {
            return 'blue';
        } else {
            return 'default';
        }
    };

    // 表格列定义
    const columns: ColumnType<StrategySignal>[] = useMemo(() => [
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
            width: 200,
            ellipsis: true,
            filterDropdown: false, // 通过外部过滤器处理
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
            title: '信号类型',
            dataIndex: 'signal_type',
            key: 'signal_type',
            width: 100,
            render: (text: string) => (
                <Tag color={getSignalTypeColor(text)}>
                    {text}
                </Tag>
            )
        },
        {
            title: 'Alpha值',
            dataIndex: 'alpha_value',
            key: 'alpha_value',
            width: 100,
            sorter: (a, b) => a.alpha_value - b.alpha_value,
            render: (value: number) => {
                const displayValue = formatAlphaValue(value);
                const meaning = getAlphaMeaning(value);

                let color = '#000000';
                if (value <= -900) {
                    color = '#999999';
                } else if (value > 0) {
                    color = '#52c41a';
                } else if (value < 0) {
                    color = '#ff4d4f';
                }

                return (
                    <Tooltip title={meaning}>
                        <Text style={{ color, fontWeight: 'bold' }}>
                            {displayValue}
                        </Text>
                    </Tooltip>
                );
            }
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
            title: '置信度',
            dataIndex: 'confidence',
            key: 'confidence',
            width: 100,
            sorter: (a, b) => a.confidence - b.confidence,
            render: (value: number) => {
                const percentage = (value * 100).toFixed(1);
                const color = value >= 0.7 ? '#52c41a' : value >= 0.5 ? '#faad14' : '#ff4d4f';

                return (
                    <Text style={{ color, fontWeight: 'bold' }}>
                        {percentage}%
                    </Text>
                );
            }
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (text: string) => {
                let color = 'default';
                if (text === 'Generated') {
                    color = 'processing';
                } else if (text === 'Executed') {
                    color = 'success';
                } else if (text === 'Failed') {
                    color = 'error';
                } else if (text === 'Cancelled') {
                    color = 'warning';
                }

                return <Tag color={color}>{text}</Tag>;
            }
        }
    ], []);

    // 分页配置
    const pagination = useMemo(() => ({
        current: 1,
        pageSize: 50,
        total: signals.length,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total: number, range: [number, number]) =>
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        pageSizeOptions: ['20', '50', '100', '200'],
        size: 'small' as const
    }), [signals.length]);

    return (
        <div className="strategy-signals-table">
            <Table<StrategySignal>
                columns={columns}
                dataSource={signals}
                loading={loading}
                pagination={pagination}
                rowKey="signal_id"
                size="small"
                scroll={{ x: 1000, y: 400 }}
                bordered
                style={{ marginTop: 16 }}
                rowClassName={(record, index) => {
                    // 根据信号类型设置行样式
                    const type = record.signal_type.toLowerCase();
                    if (['buy', 'open_long', '买入'].includes(type)) {
                        return 'signal-row-buy';
                    } else if (['sell', 'open_short', '卖出'].includes(type)) {
                        return 'signal-row-sell';
                    } else if (['close', 'close_long', 'close_short', '平仓'].includes(type)) {
                        return 'signal-row-close';
                    } else {
                        return '';
                    }
                }}
                summary={() => (
                    <Table.Summary fixed>
                        <Table.Summary.Row>
                            <Table.Summary.Cell index={0} colSpan={9}>
                                <Text strong>
                                    总计: {signals.length} 条信号
                                    {filterParams.time_range_hours && (
                                        <Text type="secondary" style={{ marginLeft: 16 }}>
                                            时间范围: 最近 {filterParams.time_range_hours} 小时
                                        </Text>
                                    )}
                                    {filterParams.max_items && (
                                        <Text type="secondary" style={{ marginLeft: 16 }}>
                                            显示上限: {filterParams.max_items} 条
                                        </Text>
                                    )}
                                </Text>
                            </Table.Summary.Cell>
                        </Table.Summary.Row>
                    </Table.Summary>
                )}
            />

            <style>{`
        .strategy-signals-table :global(.signal-row-buy) {
          background-color: #f6ffed !important;
        }
        
        .strategy-signals-table :global(.signal-row-sell) {
          background-color: #fff2f0 !important;
        }
        
        .strategy-signals-table :global(.signal-row-close) {
          background-color: #fffbe6 !important;
        }
        
        .strategy-signals-table :global(.ant-table-tbody) > :global(.ant-table-row):hover > :global(.ant-table-cell) {
          background: #e6f7ff !important;
        }
      `}</style>
        </div>
    );
}; 