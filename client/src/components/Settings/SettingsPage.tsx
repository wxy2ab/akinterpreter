import {
    ApiOutlined,
    DownloadOutlined,
    ExclamationCircleOutlined,
    ReloadOutlined,
    SaveOutlined,
    SecurityScanOutlined,
    SettingOutlined,
    UploadOutlined,
    UserOutlined
} from '@ant-design/icons';
import {
    Alert,
    Button,
    Card,
    Col,
    Divider,
    Form,
    Input,
    message,
    Modal,
    Row,
    Select,
    Space,
    Spin,
    Switch,
    Tabs,
    Typography,
    Upload
} from 'antd';
import React, { useEffect, useState } from 'react';
import { SettingsService } from '../../services/settingsService';
import { AllSettings, ConfigData } from '../../types/settings';

const { Title, Text } = Typography;
const { Option } = Select;
const { confirm } = Modal;

const SettingsPage: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [configData, setConfigData] = useState<ConfigData>({
        login: { investor: '', password: '' },
        ctp: {
            trade_addr: '',
            quote_addr: '',
            broker: '',
            appid: '',
            auth_code: '',
            simnow_symbol: ''
        }
    });

    const [appSettings, setAppSettings] = useState<AllSettings>({
        system: { theme: 'light', autoRefresh: true, language: 'zh' },
        trading: { confirmTrade: true, soundAlert: false, riskLevel: 'medium' },
        security: { autoLogoutTime: 30, rememberLogin: false, twoFactorAuth: false },
        log: { logLevel: 'info', saveLog: true, maxLogSize: 100 }
    });

    const [loginForm] = Form.useForm();
    const [ctpForm] = Form.useForm();

    // 加载配置数据
    const loadConfig = async () => {
        setLoading(true);
        try {
            const [config, settings] = await Promise.all([
                SettingsService.getConfig(),
                Promise.resolve(SettingsService.getAppSettings())
            ]);

            setConfigData(config);
            setAppSettings(settings);

            // 更新表单数据
            loginForm.setFieldsValue(config.login);
            ctpForm.setFieldsValue(config.ctp);
        } catch (error) {
            console.error('加载配置失败:', error);
            message.error('加载配置失败');
        } finally {
            setLoading(false);
        }
    };

    // 保存配置
    const saveConfig = async (values: any, type: 'login' | 'ctp') => {
        setSaving(true);
        try {
            const newConfigData = {
                ...configData,
                [type]: values
            };

            await SettingsService.saveConfig(newConfigData);
            setConfigData(newConfigData);
            message.success(`${type === 'login' ? '登录信息' : 'CTP配置'}保存成功`);
        } catch (error) {
            console.error('保存配置失败:', error);
            message.error('保存配置失败');
        } finally {
            setSaving(false);
        }
    };

    // 保存应用设置
    const saveAppSettings = (newSettings: AllSettings) => {
        try {
            SettingsService.saveAppSettings(newSettings);
            setAppSettings(newSettings);
            message.success('应用设置保存成功');
        } catch (error) {
            console.error('保存应用设置失败:', error);
            message.error('保存应用设置失败');
        }
    };

    // 测试CTP连接
    const testCTPConnection = async () => {
        try {
            const ctpConfig = ctpForm.getFieldsValue();
            const result = await SettingsService.testCTPConnection(ctpConfig);

            if (result.success) {
                message.success('CTP连接测试成功');
            } else {
                message.error(`CTP连接测试失败: ${result.message}`);
            }
        } catch (error) {
            console.error('CTP连接测试失败:', error);
            message.error('CTP连接测试失败');
        }
    };

    // 导出设置
    const exportSettings = () => {
        try {
            const settingsJson = SettingsService.exportSettings();
            const blob = new Blob([settingsJson], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `settings_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            message.success('设置已导出');
        } catch (error) {
            message.error('导出设置失败');
        }
    };

    // 导入设置
    const importSettings = (file: File) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const content = e.target?.result as string;
                const settings = SettingsService.importSettings(content);
                setAppSettings(settings);
                message.success('设置导入成功');
            } catch (error) {
                message.error('导入设置失败：格式不正确');
            }
        };
        reader.readAsText(file);
        return false; // 阻止默认上传行为
    };

    // 重置设置
    const resetSettings = () => {
        confirm({
            title: '确认重置',
            icon: <ExclamationCircleOutlined />,
            content: '确定要重置所有应用设置吗？此操作不可恢复。',
            onOk() {
                SettingsService.resetAppSettings();
                const defaultSettings = SettingsService.getAppSettings();
                setAppSettings(defaultSettings);
                message.success('设置已重置');
            },
        });
    };

    useEffect(() => {
        loadConfig();
    }, []);

    const tabItems = [
        {
            key: 'login',
            label: (
                <span>
                    <UserOutlined />
                    登录设置
                </span>
            ),
            children: (
                <Card title="登录信息配置" extra={
                    <Button icon={<ReloadOutlined />} onClick={loadConfig} loading={loading}>
                        刷新
                    </Button>
                }>
                    <Form
                        form={loginForm}
                        layout="vertical"
                        onFinish={(values) => saveConfig(values, 'login')}
                        initialValues={configData.login}
                    >
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label="投资者账号"
                                    name="investor"
                                    rules={[{ required: true, message: '请输入投资者账号' }]}
                                >
                                    <Input placeholder="请输入投资者账号" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label="密码"
                                    name="password"
                                    rules={[{ required: true, message: '请输入密码' }]}
                                >
                                    <Input.Password placeholder="请输入密码" />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Form.Item>
                            <Space>
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    icon={<SaveOutlined />}
                                    loading={saving}
                                >
                                    保存登录信息
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Card>
            )
        },
        {
            key: 'ctp',
            label: (
                <span>
                    <ApiOutlined />
                    CTP配置
                </span>
            ),
            children: (
                <Card title="CTP连接配置" extra={
                    <Space>
                        <Button onClick={testCTPConnection}>
                            测试连接
                        </Button>
                        <Button icon={<ReloadOutlined />} onClick={loadConfig} loading={loading}>
                            刷新
                        </Button>
                    </Space>
                }>
                    <Alert
                        message="CTP配置说明"
                        description="请确保所有CTP连接参数正确填写，这些参数将用于连接期货交易服务器。"
                        type="info"
                        showIcon
                        style={{ marginBottom: 16 }}
                    />

                    <Form
                        form={ctpForm}
                        layout="vertical"
                        onFinish={(values) => saveConfig(values, 'ctp')}
                        initialValues={configData.ctp}
                    >
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label="交易服务器地址"
                                    name="trade_addr"
                                    rules={[{ required: true, message: '请输入交易服务器地址' }]}
                                >
                                    <Input placeholder="例如：180.168.146.187:10131" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label="行情服务器地址"
                                    name="quote_addr"
                                    rules={[{ required: true, message: '请输入行情服务器地址' }]}
                                >
                                    <Input placeholder="例如：180.168.146.187:10111" />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label="经纪商代码"
                                    name="broker"
                                    rules={[{ required: true, message: '请输入经纪商代码' }]}
                                >
                                    <Input placeholder="例如：9999" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label="应用标识"
                                    name="appid"
                                    rules={[{ required: true, message: '请输入应用标识' }]}
                                >
                                    <Input placeholder="请输入应用标识" />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label="授权码"
                                    name="auth_code"
                                    rules={[{ required: true, message: '请输入授权码' }]}
                                >
                                    <Input placeholder="请输入授权码" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label="SimNow合约"
                                    name="simnow_symbol"
                                    tooltip="用于SimNow环境的默认合约代码"
                                >
                                    <Input placeholder="例如：rb2405" />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Form.Item>
                            <Space>
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    icon={<SaveOutlined />}
                                    loading={saving}
                                >
                                    保存CTP配置
                                </Button>
                                <Button onClick={testCTPConnection}>
                                    测试连接
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Card>
            )
        },
        {
            key: 'system',
            label: (
                <span>
                    <SettingOutlined />
                    系统设置
                </span>
            ),
            children: (
                <Card title="系统设置" extra={
                    <Space>
                        <Upload
                            accept=".json"
                            beforeUpload={importSettings}
                            showUploadList={false}
                        >
                            <Button icon={<UploadOutlined />}>导入设置</Button>
                        </Upload>
                        <Button icon={<DownloadOutlined />} onClick={exportSettings}>
                            导出设置
                        </Button>
                        <Button danger onClick={resetSettings}>
                            重置设置
                        </Button>
                    </Space>
                }>
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        <div>
                            <Title level={5}>界面设置</Title>
                            <Row gutter={16}>
                                <Col span={8}>
                                    <Space>
                                        <Text>深色主题:</Text>
                                        <Switch
                                            checked={appSettings.system.theme === 'dark'}
                                            onChange={(checked) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    system: { ...appSettings.system, theme: checked ? 'dark' as const : 'light' as const }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        />
                                    </Space>
                                </Col>
                                <Col span={8}>
                                    <Space>
                                        <Text>自动刷新:</Text>
                                        <Switch
                                            checked={appSettings.system.autoRefresh}
                                            onChange={(checked) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    system: { ...appSettings.system, autoRefresh: checked }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        />
                                    </Space>
                                </Col>
                                <Col span={8}>
                                    <Space>
                                        <Text>语言:</Text>
                                        <Select
                                            value={appSettings.system.language}
                                            style={{ width: 80 }}
                                            onChange={(value) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    system: { ...appSettings.system, language: value }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        >
                                            <Option value="zh">中文</Option>
                                            <Option value="en">English</Option>
                                        </Select>
                                    </Space>
                                </Col>
                            </Row>
                        </div>

                        <Divider />

                        <div>
                            <Title level={5}>交易设置</Title>
                            <Row gutter={16}>
                                <Col span={8}>
                                    <Space>
                                        <Text>交易确认:</Text>
                                        <Switch
                                            checked={appSettings.trading.confirmTrade}
                                            onChange={(checked) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    trading: { ...appSettings.trading, confirmTrade: checked }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        />
                                    </Space>
                                </Col>
                                <Col span={8}>
                                    <Space>
                                        <Text>声音提醒:</Text>
                                        <Switch
                                            checked={appSettings.trading.soundAlert}
                                            onChange={(checked) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    trading: { ...appSettings.trading, soundAlert: checked }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        />
                                    </Space>
                                </Col>
                                <Col span={8}>
                                    <Space>
                                        <Text>风险等级:</Text>
                                        <Select
                                            value={appSettings.trading.riskLevel}
                                            style={{ width: 80 }}
                                            onChange={(value) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    trading: { ...appSettings.trading, riskLevel: value }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        >
                                            <Option value="low">低</Option>
                                            <Option value="medium">中</Option>
                                            <Option value="high">高</Option>
                                        </Select>
                                    </Space>
                                </Col>
                            </Row>
                        </div>

                        <Divider />

                        <div>
                            <Title level={5}>日志设置</Title>
                            <Row gutter={16}>
                                <Col span={8}>
                                    <Space>
                                        <Text>日志级别:</Text>
                                        <Select
                                            value={appSettings.log.logLevel}
                                            style={{ width: 100 }}
                                            onChange={(value) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    log: { ...appSettings.log, logLevel: value }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        >
                                            <Option value="debug">DEBUG</Option>
                                            <Option value="info">INFO</Option>
                                            <Option value="warning">WARNING</Option>
                                            <Option value="error">ERROR</Option>
                                        </Select>
                                    </Space>
                                </Col>
                                <Col span={8}>
                                    <Space>
                                        <Text>保存日志:</Text>
                                        <Switch
                                            checked={appSettings.log.saveLog}
                                            onChange={(checked) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    log: { ...appSettings.log, saveLog: checked }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        />
                                    </Space>
                                </Col>
                            </Row>
                        </div>
                    </Space>
                </Card>
            )
        },
        {
            key: 'security',
            label: (
                <span>
                    <SecurityScanOutlined />
                    安全设置
                </span>
            ),
            children: (
                <Card title="安全设置">
                    <Alert
                        message="安全提醒"
                        description="为了保护您的账户安全，请定期更新密码，并确保在安全的网络环境中使用本系统。"
                        type="warning"
                        showIcon
                        style={{ marginBottom: 16 }}
                    />

                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        <div>
                            <Title level={5}>会话管理</Title>
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Space>
                                        <Text>自动登出时间:</Text>
                                        <Select
                                            value={appSettings.security.autoLogoutTime}
                                            style={{ width: 120 }}
                                            onChange={(value) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    security: { ...appSettings.security, autoLogoutTime: value }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        >
                                            <Option value={15}>15分钟</Option>
                                            <Option value={30}>30分钟</Option>
                                            <Option value={60}>1小时</Option>
                                            <Option value={0}>不自动登出</Option>
                                        </Select>
                                    </Space>
                                </Col>
                                <Col span={12}>
                                    <Space>
                                        <Text>记住登录状态:</Text>
                                        <Switch
                                            checked={appSettings.security.rememberLogin}
                                            onChange={(checked) => {
                                                const newSettings = {
                                                    ...appSettings,
                                                    security: { ...appSettings.security, rememberLogin: checked }
                                                };
                                                saveAppSettings(newSettings);
                                            }}
                                        />
                                    </Space>
                                </Col>
                            </Row>
                        </div>

                        <Divider />

                        <div>
                            <Title level={5}>密码安全</Title>
                            <Space>
                                <Button type="primary">修改密码</Button>
                                <Button
                                    type={appSettings.security.twoFactorAuth ? 'default' : 'primary'}
                                    onClick={() => {
                                        const newSettings = {
                                            ...appSettings,
                                            security: { ...appSettings.security, twoFactorAuth: !appSettings.security.twoFactorAuth }
                                        };
                                        saveAppSettings(newSettings);
                                    }}
                                >
                                    {appSettings.security.twoFactorAuth ? '禁用' : '启用'}双因子认证
                                </Button>
                            </Space>
                        </div>
                    </Space>
                </Card>
            )
        }
    ];

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <Spin size="large" tip="加载配置中..." />
            </div>
        );
    }

    return (
        <div style={{ padding: '0 0 24px 0' }}>
            <div style={{ marginBottom: 24 }}>
                <Title level={2}>
                    <SettingOutlined style={{ marginRight: 8 }} />
                    系统设置
                </Title>
                <Text type="secondary">
                    配置CTP连接参数、登录信息和系统设置
                </Text>
            </div>

            <Tabs
                defaultActiveKey="login"
                items={tabItems}
                size="large"
            />
        </div>
    );
};

export default SettingsPage; 