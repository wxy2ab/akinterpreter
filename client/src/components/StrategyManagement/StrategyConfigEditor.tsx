import {
    CheckCircleOutlined,
    EyeOutlined,
    InfoCircleOutlined,
    ReloadOutlined,
    SaveOutlined,
    SettingOutlined,
    WarningOutlined
} from '@ant-design/icons';
import {
    Alert,
    Button,
    Card,
    Col,
    Divider,
    Form,
    Input,
    InputNumber,
    message,
    Modal,
    Row,
    Select,
    Space,
    Switch,
    Table,
    Tag,
    Tooltip,
    Typography
} from 'antd';
import React, { useEffect, useState } from 'react';

const { Option } = Select;
const { Text, Title } = Typography;
const { TextArea } = Input;

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

interface StrategyConfigEditorProps {
    strategies: StrategyInfo[];
    onConfigSaved: () => void;
    loading?: boolean;
}

// 可配置的参数类型
interface ConfigParam {
    key: string;
    name: string;
    type: 'number' | 'boolean' | 'string' | 'select' | 'multiplier';
    description: string;
    defaultValue: any;
    min?: number;
    max?: number;
    step?: number;
    options?: { label: string; value: any }[];
    required?: boolean;
}

// 策略配置参数定义
const strategyConfigParams: ConfigParam[] = [
    {
        key: 'alpha_threshold',
        name: 'Alpha信号阈值',
        type: 'number',
        description: '策略信号触发的Alpha值阈值，越高越保守',
        defaultValue: 0.5,
        min: 0.1,
        max: 2.0,
        step: 0.1,
        required: true
    },
    {
        key: 'position_multiplier',
        name: '仓位系数',
        type: 'multiplier',
        description: '控制开仓数量的系数，可设置为固定数值或按合约配置',
        defaultValue: 1.0,
        required: true
    },
    {
        key: 'greed_position',
        name: '贪婪仓位模式',
        type: 'boolean',
        description: '启用后将使用贪婪算法调整仓位大小',
        defaultValue: false
    },
    {
        key: 'freq',
        name: 'K线周期',
        type: 'select',
        description: '策略使用的K线数据周期',
        defaultValue: '1m',
        options: [
            { label: '1分钟', value: '1m' },
            { label: '5分钟', value: '5m' },
            { label: '15分钟', value: '15m' },
            { label: '30分钟', value: '30m' },
            { label: '1小时', value: '1h' },
            { label: '日线', value: '1d' }
        ],
        required: true
    },
    {
        key: 'init_bars',
        name: '初始K线数',
        type: 'number',
        description: '策略初始化所需的历史K线数量',
        defaultValue: 100,
        min: 10,
        max: 1000,
        step: 10,
        required: true
    }
];

const StrategyConfigEditor: React.FC<StrategyConfigEditorProps> = ({
    strategies,
    onConfigSaved,
    loading = false
}) => {
    const [selectedStrategy, setSelectedStrategy] = useState<string>('');
    const [form] = Form.useForm();
    const [previewVisible, setPreviewVisible] = useState(false);
    const [previewData, setPreviewData] = useState<any>(null);
    const [multiplierMode, setMultiplierMode] = useState<'fixed' | 'custom'>('fixed');
    const [customMultipliers, setCustomMultipliers] = useState<{ [key: string]: number }>({});
    const [unsavedChanges, setUnsavedChanges] = useState(false);

    // 当选择的策略改变时，更新表单
    useEffect(() => {
        if (selectedStrategy) {
            const strategy = strategies.find(s => s.name === selectedStrategy);
            if (strategy) {
                // 设置表单值
                form.setFieldsValue({
                    alpha_threshold: strategy.alpha_threshold,
                    greed_position: strategy.greed_position,
                    freq: strategy.freq,
                    init_bars: strategy.init_bars
                });

                // 处理仓位系数
                if (typeof strategy.position_multiplier === 'number') {
                    setMultiplierMode('fixed');
                    form.setFieldValue('position_multiplier_fixed', strategy.position_multiplier);
                } else if (strategy.position_multiplier && typeof strategy.position_multiplier === 'object') {
                    setMultiplierMode('custom');
                    setCustomMultipliers(strategy.position_multiplier);
                } else {
                    setMultiplierMode('fixed');
                    form.setFieldValue('position_multiplier_fixed', 1.0);
                }

                setUnsavedChanges(false);
            }
        }
    }, [selectedStrategy, strategies, form]);

    // 表单值变化时标记为有未保存的修改
    const handleFormChange = () => {
        setUnsavedChanges(true);
    };

    // 预览配置
    const handlePreview = () => {
        const values = form.getFieldsValue();
        const strategy = strategies.find(s => s.name === selectedStrategy);

        if (!strategy) return;

        // 构建预览数据
        const previewConfig = {
            strategy_name: selectedStrategy,
            original_config: {
                alpha_threshold: strategy.alpha_threshold,
                position_multiplier: strategy.position_multiplier,
                greed_position: strategy.greed_position,
                freq: strategy.freq,
                init_bars: strategy.init_bars
            },
            new_config: {
                alpha_threshold: values.alpha_threshold,
                position_multiplier: multiplierMode === 'fixed'
                    ? values.position_multiplier_fixed
                    : customMultipliers,
                greed_position: values.greed_position,
                freq: values.freq,
                init_bars: values.init_bars
            }
        };

        setPreviewData(previewConfig);
        setPreviewVisible(true);
    };

    // 保存配置
    const handleSave = async () => {
        try {
            const values = await form.validateFields();

            const config = {
                alpha_threshold: values.alpha_threshold,
                position_multiplier: multiplierMode === 'fixed'
                    ? values.position_multiplier_fixed
                    : customMultipliers,
                greed_position: values.greed_position,
                freq: values.freq,
                init_bars: values.init_bars
            };

            const response = await fetch(`/api/strategy-management/strategies/${selectedStrategy}/config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config })
            });

            if (response.ok) {
                const result = await response.json();
                message.success(result.message);
                setUnsavedChanges(false);
                onConfigSaved();
            } else {
                const error = await response.json();
                throw new Error(error.detail || '保存配置失败');
            }
        } catch (error: any) {
            console.error('保存配置失败:', error);
            message.error(error.message || '保存配置失败');
        }
    };

    // 重置配置
    const handleReset = () => {
        if (selectedStrategy) {
            const strategy = strategies.find(s => s.name === selectedStrategy);
            if (strategy) {
                form.resetFields();
                setUnsavedChanges(false);
                message.info('已重置为原始配置');
            }
        }
    };

    // 添加自定义仓位系数
    const addCustomMultiplier = (symbol: string, value: number) => {
        setCustomMultipliers(prev => ({
            ...prev,
            [symbol]: value
        }));
        setUnsavedChanges(true);
    };

    // 删除自定义仓位系数
    const removeCustomMultiplier = (symbol: string) => {
        setCustomMultipliers(prev => {
            const newMultipliers = { ...prev };
            delete newMultipliers[symbol];
            return newMultipliers;
        });
        setUnsavedChanges(true);
    };

    // 获取策略可用的合约列表
    const getAvailableSymbols = () => {
        const strategy = strategies.find(s => s.name === selectedStrategy);
        return strategy ? strategy.symbols : [];
    };

    // 渲染仓位系数配置
    const renderMultiplierConfig = () => {
        return (
            <div>
                <Form.Item label="仓位系数模式">
                    <Select
                        value={multiplierMode}
                        onChange={(value) => {
                            setMultiplierMode(value);
                            setUnsavedChanges(true);
                        }}
                    >
                        <Option value="fixed">固定系数</Option>
                        <Option value="custom">按合约自定义</Option>
                    </Select>
                </Form.Item>

                {multiplierMode === 'fixed' ? (
                    <Form.Item
                        name="position_multiplier_fixed"
                        label="固定系数值"
                        rules={[{ required: true, message: '请输入仓位系数' }]}
                    >
                        <InputNumber
                            min={0.1}
                            max={10}
                            step={0.1}
                            placeholder="请输入仓位系数"
                            style={{ width: '100%' }}
                        />
                    </Form.Item>
                ) : (
                    <div>
                        <Text strong>按合约自定义系数：</Text>
                        <div style={{ marginTop: 8, marginBottom: 16 }}>
                            {Object.entries(customMultipliers).map(([symbol, value]) => (
                                <Tag
                                    key={symbol}
                                    closable
                                    onClose={() => removeCustomMultiplier(symbol)}
                                    style={{ marginBottom: 4 }}
                                >
                                    {symbol}: {value}
                                </Tag>
                            ))}
                        </div>

                        <Row gutter={8}>
                            <Col span={12}>
                                <Select
                                    placeholder="选择合约"
                                    style={{ width: '100%' }}
                                    id="symbol-select"
                                >
                                    {getAvailableSymbols().map(symbol => (
                                        <Option key={symbol} value={symbol}>{symbol}</Option>
                                    ))}
                                </Select>
                            </Col>
                            <Col span={8}>
                                <InputNumber
                                    min={0.1}
                                    max={10}
                                    step={0.1}
                                    placeholder="系数"
                                    style={{ width: '100%' }}
                                    id="multiplier-input"
                                />
                            </Col>
                            <Col span={4}>
                                <Button
                                    type="primary"
                                    size="small"
                                    onClick={() => {
                                        const symbolSelect = document.getElementById('symbol-select') as any;
                                        const multiplierInput = document.getElementById('multiplier-input') as any;

                                        if (symbolSelect?.value && multiplierInput?.value) {
                                            addCustomMultiplier(symbolSelect.value, parseFloat(multiplierInput.value));
                                            // 清空输入
                                            symbolSelect.value = '';
                                            multiplierInput.value = '';
                                        } else {
                                            message.warning('请选择合约并输入系数');
                                        }
                                    }}
                                >
                                    添加
                                </Button>
                            </Col>
                        </Row>
                    </div>
                )}
            </div>
        );
    };

    // 预览表格列定义
    const previewColumns = [
        {
            title: '参数名称',
            dataIndex: 'name',
            key: 'name',
            width: 150
        },
        {
            title: '原始值',
            dataIndex: 'original',
            key: 'original',
            width: 150,
            render: (value: any) => <Text>{String(value)}</Text>
        },
        {
            title: '新值',
            dataIndex: 'new',
            key: 'new',
            width: 150,
            render: (value: any) => <Text strong>{String(value)}</Text>
        },
        {
            title: '状态',
            key: 'status',
            width: 100,
            render: (_: any, record: any) => {
                const changed = JSON.stringify(record.original) !== JSON.stringify(record.new);
                return changed ? (
                    <Tag color="orange" icon={<WarningOutlined />}>已修改</Tag>
                ) : (
                    <Tag color="green" icon={<CheckCircleOutlined />}>未变</Tag>
                );
            }
        }
    ];

    return (
        <div className="strategy-config-editor">
            <Card title="策略配置管理" size="small">
                {/* 策略选择 */}
                <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={12}>
                        <Form.Item label="选择策略">
                            <Select
                                value={selectedStrategy}
                                onChange={setSelectedStrategy}
                                placeholder="请选择要配置的策略"
                                style={{ width: '100%' }}
                            >
                                {strategies.map(strategy => (
                                    <Option key={strategy.name} value={strategy.name}>
                                        <Space>
                                            {strategy.name}
                                            <Tag color={strategy.enabled ? 'green' : 'red'}>
                                                {strategy.enabled ? '已启用' : '已禁用'}
                                            </Tag>
                                        </Space>
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Space>
                            <Button
                                icon={<EyeOutlined />}
                                onClick={handlePreview}
                                disabled={!selectedStrategy}
                            >
                                预览配置
                            </Button>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={handleReset}
                                disabled={!selectedStrategy || !unsavedChanges}
                            >
                                重置配置
                            </Button>
                        </Space>
                    </Col>
                </Row>

                {/* 配置表单 */}
                {selectedStrategy && (
                    <>
                        {unsavedChanges && (
                            <Alert
                                message="配置已修改"
                                description="您有未保存的配置修改，请及时保存"
                                type="warning"
                                showIcon
                                style={{ marginBottom: 16 }}
                            />
                        )}

                        <Form
                            form={form}
                            layout="vertical"
                            onValuesChange={handleFormChange}
                        >
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Form.Item
                                        name="alpha_threshold"
                                        label={
                                            <Space>
                                                Alpha信号阈值
                                                <Tooltip title="策略信号触发的Alpha值阈值，越高越保守">
                                                    <InfoCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请输入Alpha阈值' }]}
                                    >
                                        <InputNumber
                                            min={0.1}
                                            max={2.0}
                                            step={0.1}
                                            placeholder="请输入Alpha阈值"
                                            style={{ width: '100%' }}
                                        />
                                    </Form.Item>
                                </Col>

                                <Col span={12}>
                                    <Form.Item
                                        name="freq"
                                        label={
                                            <Space>
                                                K线周期
                                                <Tooltip title="策略使用的K线数据周期">
                                                    <InfoCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请选择K线周期' }]}
                                    >
                                        <Select placeholder="请选择K线周期">
                                            <Option value="1m">1分钟</Option>
                                            <Option value="5m">5分钟</Option>
                                            <Option value="15m">15分钟</Option>
                                            <Option value="30m">30分钟</Option>
                                            <Option value="1h">1小时</Option>
                                            <Option value="1d">日线</Option>
                                        </Select>
                                    </Form.Item>
                                </Col>
                            </Row>

                            <Row gutter={16}>
                                <Col span={12}>
                                    <Form.Item
                                        name="init_bars"
                                        label={
                                            <Space>
                                                初始K线数
                                                <Tooltip title="策略初始化所需的历史K线数量">
                                                    <InfoCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请输入初始K线数' }]}
                                    >
                                        <InputNumber
                                            min={10}
                                            max={1000}
                                            step={10}
                                            placeholder="请输入初始K线数"
                                            style={{ width: '100%' }}
                                        />
                                    </Form.Item>
                                </Col>

                                <Col span={12}>
                                    <Form.Item
                                        name="greed_position"
                                        label={
                                            <Space>
                                                贪婪仓位模式
                                                <Tooltip title="启用后将使用贪婪算法调整仓位大小">
                                                    <InfoCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        valuePropName="checked"
                                    >
                                        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                                    </Form.Item>
                                </Col>
                            </Row>

                            <Divider />

                            {/* 仓位系数配置 */}
                            {renderMultiplierConfig()}

                            <Divider />

                            {/* 操作按钮 */}
                            <Row gutter={16}>
                                <Col span={24}>
                                    <Space>
                                        <Button
                                            type="primary"
                                            icon={<SaveOutlined />}
                                            onClick={handleSave}
                                            loading={loading}
                                            disabled={!unsavedChanges}
                                        >
                                            保存配置
                                        </Button>
                                        <Button
                                            icon={<EyeOutlined />}
                                            onClick={handlePreview}
                                        >
                                            预览修改
                                        </Button>
                                        <Button
                                            icon={<ReloadOutlined />}
                                            onClick={handleReset}
                                            disabled={!unsavedChanges}
                                        >
                                            重置
                                        </Button>
                                    </Space>
                                </Col>
                            </Row>
                        </Form>
                    </>
                )}

                {!selectedStrategy && (
                    <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <SettingOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                        <div style={{ marginTop: 16 }}>
                            <Text type="secondary">请选择要配置的策略</Text>
                        </div>
                    </div>
                )}
            </Card>

            {/* 配置预览模态框 */}
            <Modal
                title="配置预览"
                open={previewVisible}
                onCancel={() => setPreviewVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setPreviewVisible(false)}>
                        关闭
                    </Button>,
                    <Button
                        key="save"
                        type="primary"
                        icon={<SaveOutlined />}
                        onClick={() => {
                            setPreviewVisible(false);
                            handleSave();
                        }}
                        disabled={!unsavedChanges}
                    >
                        确认保存
                    </Button>
                ]}
                width={800}
            >
                {previewData && (
                    <div>
                        <Title level={5}>策略: {previewData.strategy_name}</Title>
                        <Table
                            columns={previewColumns}
                            dataSource={[
                                {
                                    name: 'Alpha信号阈值',
                                    original: previewData.original_config.alpha_threshold,
                                    new: previewData.new_config.alpha_threshold
                                },
                                {
                                    name: '仓位系数',
                                    original: previewData.original_config.position_multiplier,
                                    new: previewData.new_config.position_multiplier
                                },
                                {
                                    name: '贪婪仓位模式',
                                    original: previewData.original_config.greed_position ? '启用' : '禁用',
                                    new: previewData.new_config.greed_position ? '启用' : '禁用'
                                },
                                {
                                    name: 'K线周期',
                                    original: previewData.original_config.freq,
                                    new: previewData.new_config.freq
                                },
                                {
                                    name: '初始K线数',
                                    original: previewData.original_config.init_bars,
                                    new: previewData.new_config.init_bars
                                }
                            ]}
                            rowKey="name"
                            pagination={false}
                            size="small"
                        />
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default StrategyConfigEditor; 