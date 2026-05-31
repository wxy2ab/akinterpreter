import {
    CheckCircleOutlined,
    InfoCircleOutlined,
    SettingOutlined,
    StopOutlined,
    WarningOutlined
} from '@ant-design/icons';
import {
    Button,
    Descriptions,
    Modal,
    Space,
    Switch,
    Table,
    Tag,
    Tooltip,
    Typography,
    message
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import React, { useMemo, useState } from 'react';

const { Text } = Typography;
const { confirm } = Modal;

interface StrategyInfo {
    name: string;
    enabled: boolean;
    symbols: string[];
    alpha_threshold: number;
    position_multiplier: number | { [key: string]: number } | null;
    greed_position: boolean;
    freq: string;
    init_bars: number;
    risk_status: string;
    last_active?: string;
}

interface StrategyStatusTableProps {
    strategies: StrategyInfo[];
    onStrategyEnabledChange: () => void;
    onStrategyConfigChange: () => void;
    loading?: boolean;
}

const StrategyStatusTable: React.FC<StrategyStatusTableProps> = ({
    strategies,
    onStrategyEnabledChange,
    onStrategyConfigChange,
    loading = false
}) => {
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [selectedStrategy, setSelectedStrategy] = useState<StrategyInfo | null>(null);

    // 策略启用/禁用处理
    const handleStrategyEnabledChange = async (strategyName: string, enabled: boolean) => {
        try {
            const response = await fetch(`/api/strategy-management/strategies/${strategyName}/enable`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });

            if (response.ok) {
                const result = await response.json();
                message.success(result.message);
                onStrategyEnabledChange();
            } else {
                throw new Error('操作失败');
            }
        } catch (error) {
            console.error('切换策略状态失败:', error);
            message.error('操作失败，请重试');
        }
    };

    // 显示策略详情
    const showStrategyDetail = (strategy: StrategyInfo) => {
        setSelectedStrategy(strategy);
        setDetailModalVisible(true);
    };

    // 格式化仓位系数显示
    const formatPositionMultiplier = (multiplier: number | { [key: string]: number } | null) => {
        if (multiplier === null) {
            return <Text type="secondary">未设置</Text>;
        }

        if (typeof multiplier === 'number') {
            return <Text>{multiplier}</Text>;
        }

        if (typeof multiplier === 'object') {
            const entries = Object.entries(multiplier);
            if (entries.length <= 2) {
                return (
                    <Text>
                        {entries.map(([symbol, value]) => `${symbol}:${value}`).join(', ')}
                    </Text>
                );
            } else {
                return (
                    <Tooltip title={
                        <div>
                            {entries.map(([symbol, value]) => (
                                <div key={symbol}>{symbol}: {value}</div>
                            ))}
                        </div>
                    }>
                        <Text>多合约配置 ({entries.length})</Text>
                    </Tooltip>
                );
            }
        }

        return <Text type="secondary">-</Text>;
    };

    // 风控状态标签
    const getRiskStatusTag = (status: string) => {
        switch (status) {
            case '正常':
                return <Tag color="green" icon={<CheckCircleOutlined />}>正常</Tag>;
            case '警告':
                return <Tag color="orange" icon={<WarningOutlined />}>警告</Tag>;
            case '风控中':
                return <Tag color="red" icon={<StopOutlined />}>风控中</Tag>;
            default:
                return <Tag color="default">{status}</Tag>;
        }
    };

    // 策略活跃状态
    const getActivityStatus = (strategy: StrategyInfo) => {
        if (!strategy.enabled) {
            return <Tag color="default">已禁用</Tag>;
        }

        if (strategy.last_active) {
            const lastActiveTime = new Date(strategy.last_active);
            const now = new Date();
            const diffMinutes = (now.getTime() - lastActiveTime.getTime()) / (1000 * 60);

            if (diffMinutes < 30) {
                return <Tag color="green">活跃</Tag>;
            } else if (diffMinutes < 60) {
                return <Tag color="orange">空闲</Tag>;
            } else {
                return <Tag color="red">静默</Tag>;
            }
        }

        return <Tag color="blue">等待中</Tag>;
    };

    // 表格列定义
    const columns: ColumnsType<StrategyInfo> = [
        {
            title: '策略名称',
            dataIndex: 'name',
            key: 'name',
            width: 200,
            fixed: 'left',
            render: (name: string, record: StrategyInfo) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{name}</Text>
                    {getActivityStatus(record)}
                </Space>
            )
        },
        {
            title: '启用状态',
            dataIndex: 'enabled',
            key: 'enabled',
            width: 100,
            align: 'center',
            render: (enabled: boolean, record: StrategyInfo) => (
                <Switch
                    checked={enabled}
                    onChange={(checked) => handleStrategyEnabledChange(record.name, checked)}
                    checkedChildren="启用"
                    unCheckedChildren="禁用"
                    loading={loading}
                />
            )
        },
        {
            title: '监控品种',
            dataIndex: 'symbols',
            key: 'symbols',
            width: 180,
            render: (symbols: string[]) => (
                <div className="symbols-container">
                    {symbols.slice(0, 3).map(symbol => (
                        <Tag key={symbol} color="blue">{symbol}</Tag>
                    ))}
                    {symbols.length > 3 && (
                        <Tooltip title={symbols.slice(3).join(', ')}>
                            <Tag color="default">+{symbols.length - 3}</Tag>
                        </Tooltip>
                    )}
                </div>
            )
        },
        {
            title: '信号阈值',
            dataIndex: 'alpha_threshold',
            key: 'alpha_threshold',
            width: 100,
            align: 'center',
            render: (threshold: number) => <Text>{threshold}</Text>
        },
        {
            title: '仓位模式',
            key: 'position_mode',
            width: 120,
            align: 'center',
            render: (_, record: StrategyInfo) => (
                <Tag color={record.greed_position ? 'gold' : 'blue'}>
                    {record.greed_position ? '贪婪模式' : '动态调整'}
                </Tag>
            )
        },
        {
            title: '仓位系数',
            dataIndex: 'position_multiplier',
            key: 'position_multiplier',
            width: 140,
            render: formatPositionMultiplier
        },
        {
            title: 'K线周期',
            dataIndex: 'freq',
            key: 'freq',
            width: 80,
            align: 'center',
            render: (freq: string) => <Tag color="purple">{freq}</Tag>
        },
        {
            title: '风控状态',
            dataIndex: 'risk_status',
            key: 'risk_status',
            width: 100,
            align: 'center',
            render: getRiskStatusTag
        },
        {
            title: '操作',
            key: 'actions',
            width: 120,
            fixed: 'right',
            render: (_, record: StrategyInfo) => (
                <Space size="small">
                    <Tooltip title="查看详情">
                        <Button
                            type="text"
                            icon={<InfoCircleOutlined />}
                            onClick={() => showStrategyDetail(record)}
                            size="small"
                        />
                    </Tooltip>
                    <Tooltip title="配置策略">
                        <Button
                            type="text"
                            icon={<SettingOutlined />}
                            onClick={() => {
                                // 切换到配置选项卡并选择该策略
                                message.info('请切换到"策略配置"选项卡进行配置');
                            }}
                            size="small"
                        />
                    </Tooltip>
                </Space>
            )
        }
    ];

    // 策略详情模态框内容
    const renderStrategyDetail = () => {
        if (!selectedStrategy) return null;

        return (
            <Descriptions bordered column={2} size="small">
                <Descriptions.Item label="策略名称" span={2}>
                    <Text strong>{selectedStrategy.name}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="启用状态">
                    <Tag color={selectedStrategy.enabled ? 'green' : 'red'}>
                        {selectedStrategy.enabled ? '已启用' : '已禁用'}
                    </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="风控状态">
                    {getRiskStatusTag(selectedStrategy.risk_status)}
                </Descriptions.Item>
                <Descriptions.Item label="信号阈值">
                    {selectedStrategy.alpha_threshold}
                </Descriptions.Item>
                <Descriptions.Item label="K线周期">
                    <Tag color="purple">{selectedStrategy.freq}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="初始K线数">
                    {selectedStrategy.init_bars}
                </Descriptions.Item>
                <Descriptions.Item label="仓位模式">
                    <Tag color={selectedStrategy.greed_position ? 'gold' : 'blue'}>
                        {selectedStrategy.greed_position ? '贪婪模式' : '动态调整'}
                    </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="仓位系数" span={2}>
                    {formatPositionMultiplier(selectedStrategy.position_multiplier)}
                </Descriptions.Item>
                <Descriptions.Item label="监控品种" span={2}>
                    <Space wrap>
                        {selectedStrategy.symbols.map(symbol => (
                            <Tag key={symbol} color="blue">{symbol}</Tag>
                        ))}
                    </Space>
                </Descriptions.Item>
                {selectedStrategy.last_active && (
                    <Descriptions.Item label="最后活跃时间" span={2}>
                        {new Date(selectedStrategy.last_active).toLocaleString()}
                    </Descriptions.Item>
                )}
            </Descriptions>
        );
    };

    // 表格汇总行
    const summary = useMemo(() => {
        const totalStrategies = strategies.length;
        const enabledStrategies = strategies.filter(s => s.enabled).length;
        const riskControlledStrategies = strategies.filter(s => s.risk_status !== '正常').length;

        return (
            <Table.Summary fixed>
                <Table.Summary.Row>
                    <Table.Summary.Cell index={0}>
                        <Text strong>汇总</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={1}>
                        <Text>{enabledStrategies}/{totalStrategies}</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={2}>
                        <Text>总计 {strategies.reduce((acc, s) => acc + s.symbols.length, 0)} 个品种</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={3}>-</Table.Summary.Cell>
                    <Table.Summary.Cell index={4}>-</Table.Summary.Cell>
                    <Table.Summary.Cell index={5}>-</Table.Summary.Cell>
                    <Table.Summary.Cell index={6}>-</Table.Summary.Cell>
                    <Table.Summary.Cell index={7}>
                        <Text type={riskControlledStrategies > 0 ? 'danger' : 'success'}>
                            {riskControlledStrategies} 个风控
                        </Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={8}>-</Table.Summary.Cell>
                </Table.Summary.Row>
            </Table.Summary>
        );
    }, [strategies]);

    return (
        <div className="strategy-status-table">
            <Table
                columns={columns}
                dataSource={strategies}
                rowKey="name"
                loading={loading}
                scroll={{ x: 1200 }}
                pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 个策略`,
                }}
                summary={() => summary}
                rowClassName={(record) => {
                    if (!record.enabled) return 'strategy-row-disabled';
                    if (record.risk_status !== '正常') return 'strategy-row-risk';
                    return '';
                }}
            />

            {/* 策略详情模态框 */}
            <Modal
                title={
                    <Space>
                        <InfoCircleOutlined />
                        策略详情
                    </Space>
                }
                open={detailModalVisible}
                onCancel={() => setDetailModalVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setDetailModalVisible(false)}>
                        关闭
                    </Button>
                ]}
                width={800}
            >
                {renderStrategyDetail()}
            </Modal>
        </div>
    );
};

export default StrategyStatusTable; 