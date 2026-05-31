import {
    ApiOutlined,
    CheckCircleOutlined,
    DashboardOutlined,
    ExperimentOutlined,
    GlobalOutlined,
    SettingOutlined
} from '@ant-design/icons';
import { Alert, Button, Card, Col, Row, Space, Tag, Typography } from 'antd';
import React from 'react';

const { Title, Text, Paragraph } = Typography;

const SimpleTest: React.FC = () => {
    const currentTime = new Date().toLocaleString();

    const pageLinks = [
        {
            path: '/api/system/simple-trading',
            name: '简化交易页面',
            description: '独立的交易管理页面',
            icon: <ApiOutlined />,
            type: 'api'
        },
        {
            path: '/trading',
            name: '交易页面',
            description: 'React SPA路由页面',
            icon: <DashboardOutlined />,
            type: 'spa'
        },
        {
            path: '/trading-management',
            name: '交易管理',
            description: '完整的交易管理系统',
            icon: <SettingOutlined />,
            type: 'spa'
        },
        {
            path: '/trading-management-optimized',
            name: '优化版交易管理',
            description: '改进布局的交易管理系统',
            icon: <CheckCircleOutlined />,
            type: 'spa'
        },
        {
            path: '/debug-trading-api',
            name: 'API诊断',
            description: '交易API连接诊断工具',
            icon: <ExperimentOutlined />,
            type: 'debug'
        }
    ];

    const handleLinkClick = (path: string) => {
        window.open(path, '_blank');
    };

    const getTagColor = (type: string) => {
        switch (type) {
            case 'api': return 'blue';
            case 'spa': return 'green';
            case 'debug': return 'orange';
            default: return 'default';
        }
    };

    const getTypeLabel = (type: string) => {
        switch (type) {
            case 'api': return 'API页面';
            case 'spa': return 'SPA路由';
            case 'debug': return '调试工具';
            default: return '其他';
        }
    };

    return (
        <div style={{ padding: 24 }}>
            <Row gutter={24}>
                <Col span={24}>
                    <Card>
                        <div style={{ textAlign: 'center', marginBottom: 32 }}>
                            <Title level={1} style={{ color: '#52c41a', margin: 0 }}>
                                ✅ 服务器运行正常！
                            </Title>
                            <Paragraph style={{ fontSize: '16px', marginTop: 16 }}>
                                当前时间: <Text strong>{currentTime}</Text>
                            </Paragraph>
                        </div>

                        <Alert
                            message="系统状态正常"
                            description="Web服务器正在正常运行，所有核心功能可用"
                            type="success"
                            showIcon
                            style={{ marginBottom: 24 }}
                        />
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={24}>
                    <Card title={
                        <Space>
                            <GlobalOutlined />
                            <span>页面导航</span>
                        </Space>
                    }>
                        <Row gutter={16}>
                            {pageLinks.map((link, index) => (
                                <Col span={12} key={index} style={{ marginBottom: 16 }}>
                                    <Card
                                        size="small"
                                        hoverable
                                        style={{ cursor: 'pointer', height: '100%' }}
                                        onClick={() => handleLinkClick(link.path)}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                                            <div style={{ marginRight: 12, fontSize: '20px', color: '#1890ff' }}>
                                                {link.icon}
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                                                    <Text strong>{link.name}</Text>
                                                    <Tag color={getTagColor(link.type)}>
                                                        {getTypeLabel(link.type)}
                                                    </Tag>
                                                </div>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                                    {link.description}
                                                </Text>
                                                <div style={{ marginTop: 4 }}>
                                                    <Text code style={{ fontSize: '11px' }}>
                                                        {link.path}
                                                    </Text>
                                                </div>
                                            </div>
                                        </div>
                                    </Card>
                                </Col>
                            ))}
                        </Row>
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={12}>
                    <Card title="系统信息">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                                <Text strong>服务器状态: </Text>
                                <Tag color="success">正常运行</Tag>
                            </div>
                            <div>
                                <Text strong>当前时间: </Text>
                                <Text>{currentTime}</Text>
                            </div>
                            <div>
                                <Text strong>页面类型: </Text>
                                <Text>React测试页面</Text>
                            </div>
                            <div>
                                <Text strong>浏览器: </Text>
                                <Text code style={{ fontSize: '12px' }}>
                                    {navigator.userAgent.split('(')[0].trim()}
                                </Text>
                            </div>
                        </Space>
                    </Card>
                </Col>

                <Col span={12}>
                    <Card title="快速操作">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Button
                                type="primary"
                                block
                                onClick={() => handleLinkClick('/trading-management-optimized')}
                                icon={<CheckCircleOutlined />}
                            >
                                打开优化版交易管理
                            </Button>
                            <Button
                                block
                                onClick={() => handleLinkClick('/debug-trading-api')}
                                icon={<ExperimentOutlined />}
                            >
                                打开API诊断工具
                            </Button>
                            <Button
                                block
                                onClick={() => window.location.reload()}
                                icon={<GlobalOutlined />}
                            >
                                刷新当前页面
                            </Button>
                        </Space>
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={24}>
                    <Card title="页面说明">
                        <Alert
                            message="测试页面功能"
                            description={
                                <div>
                                    <p>这是一个简单的测试页面，用于验证系统的基本功能：</p>
                                    <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                                        <li><strong>服务器状态检测</strong>: 确认Web服务器正常运行</li>
                                        <li><strong>页面导航测试</strong>: 测试各个功能页面的可访问性</li>
                                        <li><strong>路由系统验证</strong>: 验证SPA路由和API端点都工作正常</li>
                                        <li><strong>快速故障排除</strong>: 提供便捷的诊断工具入口</li>
                                    </ul>
                                </div>
                            }
                            type="info"
                            showIcon
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default SimpleTest; 