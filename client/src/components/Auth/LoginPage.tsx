import { Button, Card, Form, Input, message, Spin, Typography } from 'antd';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

interface LoginForm {
    investor: string;
    password: string;
}

interface LoginInfo {
    investor: string;
    password: string;
}

interface LoginPageProps {
    onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [configLoading, setConfigLoading] = useState(true);
    const [form] = Form.useForm();
    const navigate = useNavigate();

    // 页面加载时读取配置文件中的登录信息
    useEffect(() => {
        loadLoginInfo();
    }, []);

    const loadLoginInfo = async () => {
        setConfigLoading(true);
        try {
            const response = await axios.get('/api/config/login-info');
            if (response.data) {
                form.setFieldsValue({
                    investor: response.data.investor || '',
                    password: response.data.password || ''
                });
            }
        } catch (error) {
            console.error('加载登录信息失败:', error);
            message.warning('加载配置信息失败，请手动输入');
        } finally {
            setConfigLoading(false);
        }
    };

    const onFinish = async (values: LoginForm) => {
        setLoading(true);

        try {
            // 1. 先验证登录信息并获取CTP配置
            const loginResponse = await axios.post('/api/config/login', {
                investor: values.investor,
                password: values.password
            });

            if (loginResponse.data.success) {
                message.success('登录验证成功，正在启动CTP服务...');

                // 2. 使用返回的配置启动CTP服务
                const ctpResponse = await axios.post('/api/system/start-ctp', loginResponse.data.config);

                if (ctpResponse.data.success) {
                    message.success('CTP服务启动成功');
                    // 保存登录状态到localStorage
                    localStorage.setItem('currentUser', values.investor);
                    localStorage.setItem('isLoggedIn', 'true');
                    // 调用成功回调
                    if (onLoginSuccess) {
                        onLoginSuccess();
                    }
                    navigate('/dashboard');
                } else {
                    message.error('CTP服务启动失败: ' + ctpResponse.data.message);
                }
            } else {
                message.error(loginResponse.data.message || '登录验证失败');
            }
        } catch (error: any) {
            console.error('登录失败:', error);
            if (error.response?.status === 400) {
                message.error(error.response.data.detail || '登录参数错误');
            } else {
                message.error('登录失败，请检查网络连接');
            }
        } finally {
            setLoading(false);
        }
    };

    const showSettings = () => {
        message.info('设置功能正在开发中。当前配置文件路径: gui/setting.ini，请直接编辑配置文件来修改CTP连接参数。');
    };

    if (configLoading) {
        return (
            <div style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}>
                <Card style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>
                        <Text>正在加载配置信息...</Text>
                    </div>
                </Card>
            </div>
        );
    }

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '20px'
        }}>
            <Card
                style={{
                    width: '100%',
                    maxWidth: 400,
                    boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
                }}
            >
                <div style={{ textAlign: 'center', marginBottom: 32 }}>
                    <Title level={2} style={{ color: '#1890ff', marginBottom: 8 }}>
                        CTP Web Trading System
                    </Title>
                    <Text type="secondary">
                        期货交易系统 - Web版
                    </Text>
                </div>

                <Form
                    form={form}
                    layout="vertical"
                    onFinish={onFinish}
                    size="large"
                >
                    <Form.Item
                        label="投资者账号"
                        name="investor"
                        rules={[{ required: true, message: '请输入投资者账号' }]}
                    >
                        <Input
                            placeholder="请输入投资者账号"
                            style={{ height: 48 }}
                        />
                    </Form.Item>

                    <Form.Item
                        label="密码"
                        name="password"
                        rules={[{ required: true, message: '请输入密码' }]}
                    >
                        <Input.Password
                            placeholder="请输入密码"
                            style={{ height: 48 }}
                        />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 16 }}>
                        <Button
                            type="primary"
                            htmlType="submit"
                            loading={loading}
                            style={{
                                width: '100%',
                                height: 48,
                                fontSize: 16,
                                fontWeight: 500
                            }}
                        >
                            {loading ? '登录中...' : '登录'}
                        </Button>
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0 }}>
                        <Button
                            type="default"
                            onClick={showSettings}
                            style={{
                                width: '100%',
                                height: 40
                            }}
                        >
                            设置
                        </Button>
                    </Form.Item>
                </Form>

                <div style={{ textAlign: 'center', marginTop: 20 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        * 配置信息从 gui/setting.ini 读取
                    </Text>
                </div>
            </Card>
        </div>
    );
};

export default LoginPage; 