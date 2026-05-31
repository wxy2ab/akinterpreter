import {
    ClearOutlined,
    DeleteOutlined,
    ExportOutlined,
    InfoCircleOutlined,
    PlusOutlined
} from '@ant-design/icons';
import {
    Button,
    Card,
    Col,
    Divider,
    Form,
    Input,
    message,
    Modal,
    Popconfirm,
    Row,
    Select,
    Space,
    Table,
    Tag,
    Tooltip,
    Typography
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import React, { useMemo, useState } from 'react';

const { Text } = Typography;
const { Option } = Select;
const { confirm } = Modal;

interface MonitoredSymbol {
    symbol: string;
    product: string;
    strategy_name: string;
    added_time: string;
}

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
}

interface SymbolMonitoringTableProps {
    symbols: MonitoredSymbol[];
    strategies: StrategyInfo[];
    onSymbolAdded: () => void;
    onSymbolRemoved: () => void;
    loading?: boolean;
}

const SymbolMonitoringTable: React.FC<SymbolMonitoringTableProps> = ({
    symbols,
    strategies,
    onSymbolAdded,
    onSymbolRemoved,
    loading = false
}) => {
    const [addModalVisible, setAddModalVisible] = useState(false);
    const [batchModalVisible, setBatchModalVisible] = useState(false);
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
    const [form] = Form.useForm();
    const [batchForm] = Form.useForm();

    // 添加单个合约
    const handleAddSymbol = async (values: { symbol: string }) => {
        try {
            const response = await fetch(`/api/strategy-management/symbols/${values.symbol}`, {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                message.success(result.message);
                onSymbolAdded();
                setAddModalVisible(false);
                form.resetFields();
            } else {
                const error = await response.json();
                throw new Error(error.detail || '添加合约失败');
            }
        } catch (error: any) {
            console.error('添加合约失败:', error);
            message.error(error.message || '添加合约失败');
        }
    };

    // 删除单个合约
    const handleRemoveSymbol = async (symbol: string) => {
        try {
            const response = await fetch(`/api/strategy-management/symbols/${symbol}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                const result = await response.json();
                message.success(result.message);
                onSymbolRemoved();
            } else {
                const error = await response.json();
                throw new Error(error.detail || '删除合约失败');
            }
        } catch (error: any) {
            console.error('删除合约失败:', error);
            message.error(error.message || '删除合约失败');
        }
    };

    // 批量删除选中的合约
    const handleBatchRemove = async () => {
        if (selectedRowKeys.length === 0) {
            message.warning('请先选择要删除的合约');
            return;
        }

        confirm({
            title: '确认批量删除',
            content: `确定要删除选中的 ${selectedRowKeys.length} 个合约吗？`,
            onOk: async () => {
                try {
                    const promises = selectedRowKeys.map(symbol =>
                        fetch(`/api/strategy-management/symbols/${symbol}`, { method: 'DELETE' })
                    );

                    await Promise.all(promises);
                    message.success(`已删除 ${selectedRowKeys.length} 个合约`);
                    setSelectedRowKeys([]);
                    onSymbolRemoved();
                } catch (error) {
                    console.error('批量删除失败:', error);
                    message.error('批量删除失败');
                }
            }
        });
    };

    // 清空所有合约
    const handleClearAll = async () => {
        confirm({
            title: '确认清空所有合约',
            content: '这将删除所有监控合约，确定继续吗？',
            type: 'warning',
            onOk: async () => {
                try {
                    const response = await fetch('/api/strategy-management/symbols', {
                        method: 'DELETE'
                    });

                    if (response.ok) {
                        const result = await response.json();
                        message.success(result.message);
                        onSymbolRemoved();
                    } else {
                        throw new Error('清空合约失败');
                    }
                } catch (error) {
                    console.error('清空合约失败:', error);
                    message.error('清空合约失败');
                }
            }
        });
    };

    // 导出合约列表
    const handleExport = async (format: 'csv' | 'json') => {
        try {
            const response = await fetch(`/api/strategy-management/symbols/export?format=${format}`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `monitored_symbols_${new Date().toISOString().slice(0, 10)}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                message.success('导出成功');
            } else {
                throw new Error('导出失败');
            }
        } catch (error) {
            console.error('导出失败:', error);
            message.error('导出失败');
        }
    };

    // 批量添加合约
    const handleBatchAdd = async (values: { symbols: string }) => {
        try {
            const symbolList = values.symbols
                .split(/[,，\s\n]+/)
                .map(s => s.trim().toUpperCase())
                .filter(s => s.length > 0);

            if (symbolList.length === 0) {
                message.warning('请输入有效的合约代码');
                return;
            }

            let successCount = 0;
            let failedCount = 0;
            const failedSymbols: string[] = [];

            for (const symbol of symbolList) {
                try {
                    const response = await fetch(`/api/strategy-management/symbols/${symbol}`, {
                        method: 'POST'
                    });

                    if (response.ok) {
                        successCount++;
                    } else {
                        failedCount++;
                        failedSymbols.push(symbol);
                    }
                } catch (error) {
                    failedCount++;
                    failedSymbols.push(symbol);
                }
            }

            message.success(`批量添加完成：成功 ${successCount} 个，失败 ${failedCount} 个`);

            if (failedSymbols.length > 0) {
                console.warn('添加失败的合约:', failedSymbols);
            }

            onSymbolAdded();
            setBatchModalVisible(false);
            batchForm.resetFields();
        } catch (error) {
            console.error('批量添加失败:', error);
            message.error('批量添加失败');
        }
    };

    // 获取策略名称显示
    const getStrategyDisplay = (strategyName: string) => {
        const strategy = strategies.find(s => s.name === strategyName);
        if (!strategy) {
            return <Tag color="default">{strategyName}</Tag>;
        }

        const color = strategy.enabled ? (strategy.risk_status === '正常' ? 'green' : 'orange') : 'red';
        return (
            <Tooltip title={`阈值: ${strategy.alpha_threshold}, 模式: ${strategy.greed_position ? '贪婪' : '动态'}`}>
                <Tag color={color}>{strategyName}</Tag>
            </Tooltip>
        );
    };

    // 表格列定义
    const columns: ColumnsType<MonitoredSymbol> = [
        {
            title: '合约代码',
            dataIndex: 'symbol',
            key: 'symbol',
            width: 120,
            sorter: (a, b) => a.symbol.localeCompare(b.symbol),
            render: (symbol: string) => <Text strong>{symbol}</Text>
        },
        {
            title: '品种代码',
            dataIndex: 'product',
            key: 'product',
            width: 100,
            sorter: (a, b) => a.product.localeCompare(b.product),
            render: (product: string) => <Tag color="blue">{product}</Tag>
        },
        {
            title: '对应策略',
            dataIndex: 'strategy_name',
            key: 'strategy_name',
            width: 180,
            render: getStrategyDisplay
        },
        {
            title: '添加时间',
            dataIndex: 'added_time',
            key: 'added_time',
            width: 160,
            sorter: (a, b) => new Date(a.added_time).getTime() - new Date(b.added_time).getTime(),
            render: (time: string) => new Date(time).toLocaleString()
        },
        {
            title: '操作',
            key: 'actions',
            width: 100,
            render: (_, record: MonitoredSymbol) => (
                <Popconfirm
                    title="确定删除此合约？"
                    description="删除后将停止监控该合约"
                    onConfirm={() => handleRemoveSymbol(record.symbol)}
                    okText="确定"
                    cancelText="取消"
                >
                    <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        size="small"
                    />
                </Popconfirm>
            )
        }
    ];

    // 行选择配置
    const rowSelection = {
        selectedRowKeys,
        onChange: (selectedKeys: React.Key[]) => {
            setSelectedRowKeys(selectedKeys);
        },
        getCheckboxProps: (record: MonitoredSymbol) => ({
            name: record.symbol,
        }),
    };

    // 统计信息
    const statisticsData = useMemo(() => {
        const productCounts = symbols.reduce((acc, symbol) => {
            acc[symbol.product] = (acc[symbol.product] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const strategyCounts = symbols.reduce((acc, symbol) => {
            acc[symbol.strategy_name] = (acc[symbol.strategy_name] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        return {
            totalSymbols: symbols.length,
            productCounts,
            strategyCounts,
            topProducts: Object.entries(productCounts)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5),
            topStrategies: Object.entries(strategyCounts)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
        };
    }, [symbols]);

    return (
        <div className="symbol-monitoring-table">
            {/* 控制面板 */}
            <Card title="合约监控管理" size="small" style={{ marginBottom: 16 }}>
                <Row gutter={[16, 16]}>
                    <Col span={12}>
                        <Space wrap>
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                onClick={() => setAddModalVisible(true)}
                            >
                                添加合约
                            </Button>
                            <Button
                                icon={<PlusOutlined />}
                                onClick={() => setBatchModalVisible(true)}
                            >
                                批量添加
                            </Button>
                            <Button
                                danger
                                icon={<DeleteOutlined />}
                                onClick={handleBatchRemove}
                                disabled={selectedRowKeys.length === 0}
                            >
                                批量删除 ({selectedRowKeys.length})
                            </Button>
                            <Button
                                danger
                                icon={<ClearOutlined />}
                                onClick={handleClearAll}
                                disabled={symbols.length === 0}
                            >
                                清空全部
                            </Button>
                        </Space>
                    </Col>
                    <Col span={12}>
                        <Space wrap style={{ float: 'right' }}>
                            <Button
                                icon={<ExportOutlined />}
                                onClick={() => handleExport('csv')}
                                disabled={symbols.length === 0}
                            >
                                导出CSV
                            </Button>
                            <Button
                                icon={<ExportOutlined />}
                                onClick={() => handleExport('json')}
                                disabled={symbols.length === 0}
                            >
                                导出JSON
                            </Button>
                        </Space>
                    </Col>
                </Row>

                {/* 统计信息 */}
                <Divider />
                <Row gutter={16}>
                    <Col span={8}>
                        <div className="stat-summary">
                            <Text strong>总合约数：</Text>
                            <Text>{statisticsData.totalSymbols}</Text>
                        </div>
                    </Col>
                    <Col span={8}>
                        <div className="stat-summary">
                            <Text strong>品种分布：</Text>
                            <Space wrap>
                                {statisticsData.topProducts.map(([product, count]) => (
                                    <Tag key={product} color="blue">{product}({count})</Tag>
                                ))}
                            </Space>
                        </div>
                    </Col>
                    <Col span={8}>
                        <div className="stat-summary">
                            <Text strong>策略分布：</Text>
                            <Space wrap>
                                {statisticsData.topStrategies.map(([strategy, count]) => (
                                    <Tag key={strategy} color="green">{strategy}({count})</Tag>
                                ))}
                            </Space>
                        </div>
                    </Col>
                </Row>
            </Card>

            {/* 合约表格 */}
            <Table
                columns={columns}
                dataSource={symbols}
                rowKey="symbol"
                loading={loading}
                rowSelection={rowSelection}
                pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 个合约`,
                }}
            />

            {/* 添加单个合约模态框 */}
            <Modal
                title="添加监控合约"
                open={addModalVisible}
                onCancel={() => {
                    setAddModalVisible(false);
                    form.resetFields();
                }}
                footer={null}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleAddSymbol}
                >
                    <Form.Item
                        name="symbol"
                        label="合约代码"
                        rules={[
                            { required: true, message: '请输入合约代码' },
                            { pattern: /^[A-Z]{1,4}[0-9]{4}$/, message: '请输入正确的合约代码格式，如IF2506' }
                        ]}
                    >
                        <Input
                            placeholder="请输入合约代码，如IF2506"
                            style={{ textTransform: 'uppercase' }}
                        />
                    </Form.Item>
                    <Form.Item>
                        <Space>
                            <Button type="primary" htmlType="submit">
                                添加
                            </Button>
                            <Button onClick={() => setAddModalVisible(false)}>
                                取消
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* 批量添加合约模态框 */}
            <Modal
                title="批量添加监控合约"
                open={batchModalVisible}
                onCancel={() => {
                    setBatchModalVisible(false);
                    batchForm.resetFields();
                }}
                footer={null}
                width={600}
            >
                <Form
                    form={batchForm}
                    layout="vertical"
                    onFinish={handleBatchAdd}
                >
                    <Form.Item
                        name="symbols"
                        label="合约代码列表"
                        rules={[{ required: true, message: '请输入合约代码' }]}
                    >
                        <Input.TextArea
                            rows={6}
                            placeholder="请输入合约代码，支持多种分隔符：&#10;IF2506, IC2506&#10;AU2506 AG2506&#10;HC2506&#10;RB2506"
                            style={{ textTransform: 'uppercase' }}
                        />
                    </Form.Item>
                    <Form.Item>
                        <Text type="secondary">
                            <InfoCircleOutlined /> 支持逗号、空格、换行等分隔符，会自动转换为大写并去重
                        </Text>
                    </Form.Item>
                    <Form.Item>
                        <Space>
                            <Button type="primary" htmlType="submit">
                                批量添加
                            </Button>
                            <Button onClick={() => setBatchModalVisible(false)}>
                                取消
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default SymbolMonitoringTable; 