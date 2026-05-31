import {
    AlertOutlined,
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    MinusCircleOutlined,
    SafetyCertificateOutlined, // 替换 ShieldCheckOutlined
    StopOutlined,
    FallOutlined, // 替换 TrendingDownOutlined
    RiseOutlined, // 替换 TrendingUpOutlined
    WarningOutlined
} from '@ant-design/icons';
import {
    Alert,
    Badge,
    Button,
    Card,
    Col,
    Form,
    InputNumber,
    List,
    Modal,
    Progress,
    Row,
    Space,
    Statistic,
    Switch,
    Tag,
    Tooltip,
    Typography,
    message
} from 'antd';
import React, { useMemo, useState } from 'react';

const { Text, Title } = Typography;
const { confirm } = Modal;

interface RiskConfig {
    enabled: boolean;
    max_order_size: number;
    max_position_size: number;
    stop_loss_pct: number;
    daily_loss_limit: number;
}

interface RiskStatus {
    enabled: boolean;
    daily_pnl: number;
    current_position: number;
    risk_level: string;
    last_updated: string;
}

interface RiskManagementPanelProps {
    config: RiskConfig;
    status: RiskStatus;
    onConfigChange: () => void;
    onStatusChange: () => void;
    loading?: boolean;
}

// 风险等级配置
const riskLevels = {
    '正常': { color: 'green', icon: CheckCircleOutlined },
    '注意': { color: 'blue', icon: CheckCircleOutlined },
    '警告': { color: 'orange', icon: WarningOutlined },
    '危险': { color: 'red', icon: AlertOutlined },
    '严重': { color: 'red', icon: StopOutlined }
};

const RiskManagementPanel: React.FC<RiskManagementPanelProps> = ({
    config,
    status,
    onConfigChange,
    onStatusChange,
    loading = false
}) => {
    const [form] = Form.useForm();
    const [unsavedChanges, setUnsavedChanges] = useState(false);

    // 初始化表单
    React.useEffect(() => {
        form.setFieldsValue(config);
        setUnsavedChanges(false);
    }, [config, form]);

    // 计算风险指标
    const riskMetrics = useMemo(() => {
        const dailyLossRatio = Math.abs(status.daily_pnl) / config.daily_loss_limit * 100;
        const positionRatio = Math.abs(status.current_position) / config.max_position_size * 100;

        return {
            dailyLossRatio: Math.min(dailyLossRatio, 100),
            positionRatio: Math.min(positionRatio, 100),
            isProfitable: status.daily_pnl >= 0,
            riskScore: Math.max(dailyLossRatio, positionRatio)
        };
    }, [status, config]);

    // 获取风险状态颜色和图标
    const getRiskLevelDisplay = (level: string) => {
        const levelConfig = riskLevels[level as keyof typeof riskLevels] || riskLevels['正常'];
        const IconComponent = levelConfig.icon;
        return {
            color: levelConfig.color,
            icon: <IconComponent />
        };
    };

    // 保存风控配置
    const handleSaveConfig = async () => {
        try {
            const values = await form.validateFields();

            const response = await fetch('/api/strategy-management/risk/config', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: values })
            });

            if (response.ok) {
                const result = await response.json();
                message.success(result.message);
                setUnsavedChanges(false);
                onConfigChange();
            } else {
                const error = await response.json();
                throw new Error(error.detail || '保存配置失败');
            }
        } catch (error: any) {
            console.error('保存风控配置失败:', error);
            message.error(error.message || '保存风控配置失败');
        }
    };

    // 紧急停止
    const handleEmergencyStop = () => {
        confirm({
            title: '确认紧急停止？',
            content: '这将立即停止所有策略的自动交易，是否继续？',
            icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
            okText: '确认停止',
            okType: 'danger',
            cancelText: '取消',
            onOk: async () => {
                try {
                    const response = await fetch('/api/strategy-management/risk/emergency-stop', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ reason: '用户手动触发紧急停止' })
                    });

                    if (response.ok) {
                        const result = await response.json();
                        message.success(result.message);
                        onStatusChange();
                    } else {
                        throw new Error('紧急停止失败');
                    }
                } catch (error) {
                    console.error('紧急停止失败:', error);
                    message.error('紧急停止失败');
                }
            }
        });
    };

    // 重置风控状态
    const handleResetRisk = () => {
        confirm({
            title: '确认重置风控状态？',
            content: '这将重置当日盈亏等风控指标，是否继续？',
            onOk: async () => {
                try {
                    const response = await fetch('/api/strategy-management/risk/reset', {
                        method: 'POST'
                    });

                    if (response.ok) {
                        const result = await response.json();
                        message.success(result.message);
                        onStatusChange();
                    } else {
                        throw new Error('重置风控状态失败');
                    }
                } catch (error) {
                    console.error('重置风控状态失败:', error);
                    message.error('重置风控状态失败');
                }
            }
        });
    };

    // 表单值变化处理
    const handleFormChange = () => {
        setUnsavedChanges(true);
    };

    // 获取进度条颜色
    const getProgressColor = (ratio: number) => {
        if (ratio < 50) return '#52c41a';
        if (ratio < 75) return '#faad14';
        return '#ff4d4f';
    };

    return (
        <div className="risk-management-panel">
            <Row gutter={[16, 16]}>
                {/* 风控状态概览 */}
                <Col span={24}>
                    <Card
                        title={
                            <Space>
                                <SafetyCertificateOutlined />
                                风控状态概览
                                <Badge
                                    status={status.enabled ? 'processing' : 'default'}
                                    text={status.enabled ? '运行中' : '已停用'}
                                />
                            </Space>
                        }
                        size="small"
                    >
                        <Row gutter={16}>
                            <Col span={6}>
                                <Statistic
                                    title="当日盈亏"
                                    value={status.daily_pnl}
                                    precision={2}
                                    valueStyle={{
                                        color: riskMetrics.isProfitable ? '#3f8600' : '#cf1322'
                                    }}
                                    prefix={riskMetrics.isProfitable ?
                                        <RiseOutlined /> :
                                        <FallOutlined />
                                    }
                                    suffix="¥"
                                />
                            </Col>
                            <Col span={6}>
                                <Statistic
                                    title="当前持仓"
                                    value={Math.abs(status.current_position)}
                                    valueStyle={{ color: '#1890ff' }}
                                    suffix="手"
                                />
                            </Col>
                            <Col span={6}>
                                <div>
                                    <Text type="secondary">风险等级</Text>
                                    <div style={{ marginTop: 4 }}>
                                        <Tag
                                            color={getRiskLevelDisplay(status.risk_level).color}
                                            icon={getRiskLevelDisplay(status.risk_level).icon}
                                            style={{ fontSize: 14, padding: '4px 8px' }}
                                        >
                                            {status.risk_level}
                                        </Tag>
                                    </div>
                                </div>
                            </Col>
                            <Col span={6}>
                                <div>
                                    <Text type="secondary">最后更新</Text>
                                    <div style={{ marginTop: 4 }}>
                                        <Text>{new Date(status.last_updated).toLocaleString()}</Text>
                                    </div>
                                </div>
                            </Col>
                        </Row>
                    </Card>
                </Col>

                {/* 风险指标监控 */}
                <Col span={12}>
                    <Card title="风险指标监控" size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                                <Row justify="space-between">
                                    <Text>当日亏损比例</Text>
                                    <Text strong>{riskMetrics.dailyLossRatio.toFixed(1)}%</Text>
                                </Row>
                                <Progress
                                    percent={riskMetrics.dailyLossRatio}
                                    strokeColor={getProgressColor(riskMetrics.dailyLossRatio)}
                                    size="small"
                                />
                            </div>

                            <div>
                                <Row justify="space-between">
                                    <Text>持仓占用比例</Text>
                                    <Text strong>{riskMetrics.positionRatio.toFixed(1)}%</Text>
                                </Row>
                                <Progress
                                    percent={riskMetrics.positionRatio}
                                    strokeColor={getProgressColor(riskMetrics.positionRatio)}
                                    size="small"
                                />
                            </div>

                            <div>
                                <Row justify="space-between">
                                    <Text>综合风险评分</Text>
                                    <Text strong>{riskMetrics.riskScore.toFixed(1)}</Text>
                                </Row>
                                <Progress
                                    percent={riskMetrics.riskScore}
                                    strokeColor={getProgressColor(riskMetrics.riskScore)}
                                    size="small"
                                />
                            </div>
                        </Space>
                    </Card>
                </Col>

                {/* 紧急控制 */}
                <Col span={12}>
                    <Card title="紧急控制" size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Alert
                                message="紧急停止功能"
                                description="立即停止所有策略的自动交易"
                                type="warning"
                                showIcon
                                style={{ marginBottom: 12 }}
                            />

                            <Button
                                type="primary"
                                danger
                                size="large"
                                icon={<StopOutlined />}
                                onClick={handleEmergencyStop}
                                style={{ width: '100%', marginBottom: 8 }}
                            >
                                紧急停止交易
                            </Button>

                            <Button
                                type="default"
                                icon={<MinusCircleOutlined />}
                                onClick={handleResetRisk}
                                style={{ width: '100%' }}
                            >
                                重置风控状态
                            </Button>
                        </Space>
                    </Card>
                </Col>

                {/* 风控配置 */}
                <Col span={24}>
                    <Card
                        title="风控配置"
                        size="small"
                        extra={
                            <Space>
                                <Button
                                    type="primary"
                                    onClick={handleSaveConfig}
                                    disabled={!unsavedChanges}
                                    loading={loading}
                                >
                                    保存配置
                                </Button>
                                <Button
                                    onClick={() => {
                                        form.resetFields();
                                        setUnsavedChanges(false);
                                    }}
                                    disabled={!unsavedChanges}
                                >
                                    重置
                                </Button>
                            </Space>
                        }
                    >
                        {unsavedChanges && (
                            <Alert
                                message="配置已修改"
                                description="您有未保存的配置修改，请及时保存"
                                type="info"
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
                                <Col span={6}>
                                    <Form.Item
                                        name="enabled"
                                        label={
                                            <Space>
                                                启用风控
                                                <Tooltip title="是否启用风险控制功能">
                                                    <ExclamationCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        valuePropName="checked"
                                    >
                                        <Switch
                                            checkedChildren="启用"
                                            unCheckedChildren="禁用"
                                            size="default"
                                        />
                                    </Form.Item>
                                </Col>

                                <Col span={6}>
                                    <Form.Item
                                        name="max_order_size"
                                        label={
                                            <Space>
                                                单笔最大下单量
                                                <Tooltip title="单次下单的最大手数限制">
                                                    <ExclamationCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请输入最大下单量' }]}
                                    >
                                        <InputNumber
                                            min={1}
                                            max={100}
                                            placeholder="最大下单量"
                                            style={{ width: '100%' }}
                                            addonAfter="手"
                                        />
                                    </Form.Item>
                                </Col>

                                <Col span={6}>
                                    <Form.Item
                                        name="max_position_size"
                                        label={
                                            <Space>
                                                最大持仓量
                                                <Tooltip title="允许的最大总持仓手数">
                                                    <ExclamationCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请输入最大持仓量' }]}
                                    >
                                        <InputNumber
                                            min={1}
                                            max={1000}
                                            placeholder="最大持仓量"
                                            style={{ width: '100%' }}
                                            addonAfter="手"
                                        />
                                    </Form.Item>
                                </Col>

                                <Col span={6}>
                                    <Form.Item
                                        name="stop_loss_pct"
                                        label={
                                            <Space>
                                                止损百分比
                                                <Tooltip title="单笔交易的止损百分比">
                                                    <ExclamationCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请输入止损百分比' }]}
                                    >
                                        <InputNumber
                                            min={0.5}
                                            max={10}
                                            step={0.1}
                                            placeholder="止损百分比"
                                            style={{ width: '100%' }}
                                            addonAfter="%"
                                        />
                                    </Form.Item>
                                </Col>
                            </Row>

                            <Row gutter={16}>
                                <Col span={6}>
                                    <Form.Item
                                        name="daily_loss_limit"
                                        label={
                                            <Space>
                                                日亏损限额
                                                <Tooltip title="单日最大亏损金额限制">
                                                    <ExclamationCircleOutlined />
                                                </Tooltip>
                                            </Space>
                                        }
                                        rules={[{ required: true, message: '请输入日亏损限额' }]}
                                    >
                                        <InputNumber
                                            min={1000}
                                            max={1000000}
                                            step={1000}
                                            placeholder="日亏损限额"
                                            style={{ width: '100%' }}
                                            addonAfter="¥"
                                        />
                                    </Form.Item>
                                </Col>
                            </Row>
                        </Form>
                    </Card>
                </Col>

                {/* 风控规则说明 */}
                <Col span={24}>
                    <Card title="风控规则说明" size="small">
                        <List
                            size="small"
                            dataSource={[
                                '当日亏损超过设定限额时，系统将自动停止所有策略',
                                '持仓量超过最大限制时，将拒绝新的开仓指令',
                                '单笔下单量超过限制时，将按最大允许量执行',
                                '风险等级根据当前亏损和持仓情况动态计算',
                                '紧急停止功能将立即停止所有自动交易'
                            ]}
                            renderItem={(item, index) => (
                                <List.Item>
                                    <Space>
                                        <Badge color="blue" />
                                        <Text>{item}</Text>
                                    </Space>
                                </List.Item>
                            )}
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default RiskManagementPanel; 