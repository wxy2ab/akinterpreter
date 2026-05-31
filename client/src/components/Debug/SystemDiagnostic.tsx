import {
    ApiOutlined,
    ClearOutlined,
    ExperimentOutlined,
    FileTextOutlined,
    GlobalOutlined,
    PlayCircleOutlined
} from '@ant-design/icons';
import { Alert, Button, Card, Col, Progress, Row, Space, Typography } from 'antd';
import React, { useEffect, useRef, useState } from 'react';

const { Title, Text, Paragraph } = Typography;

interface TestResult {
    name: string;
    url: string;
    status: 'pending' | 'running' | 'success' | 'error';
    response?: any;
    error?: string;
    timestamp?: string;
}

const SystemDiagnostic: React.FC = () => {
    const [testResults, setTestResults] = useState<TestResult[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [currentTest, setCurrentTest] = useState<string>('');
    const logsRef = useRef<HTMLDivElement>(null);

    const addLog = (message: string, type: 'info' | 'success' | 'error' | 'warning' = 'info') => {
        const time = new Date().toLocaleTimeString();
        const colorMap = {
            info: '#1890ff',
            success: '#52c41a',
            error: '#f5222d',
            warning: '#fa8c16'
        };
        const styledMessage = `<span style="color: ${colorMap[type]}; font-weight: bold;">[${time}] ${message}</span>`;
        setLogs(prev => [...prev, styledMessage]);
    };

    const clearLog = () => {
        setLogs([]);
    };

    const scrollToBottom = () => {
        if (logsRef.current) {
            logsRef.current.scrollTop = logsRef.current.scrollHeight;
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [logs]);

    const testAPI = async () => {
        addLog('开始测试API连接...', 'info');

        const apis = [
            '/api/trading-management/positions',
            '/api/trading-management/trades',
            '/api/trading-management/account'
        ];

        for (const api of apis) {
            setCurrentTest(api);
            try {
                const response = await fetch(api);
                const data = await response.json();

                if (response.ok) {
                    addLog(`✅ ${api} - 正常 (${response.status})`, 'success');
                    const dataType = Array.isArray(data) ? `Array[${data.length}]` : typeof data;
                    addLog(`   数据: ${dataType}`, 'info');
                } else {
                    addLog(`❌ ${api} - 错误 (${response.status})`, 'error');
                }
            } catch (error) {
                addLog(`❌ ${api} - 失败: ${error instanceof Error ? error.message : '未知错误'}`, 'error');
            }
        }
        setCurrentTest('');
    };

    const testPages = async () => {
        addLog('开始测试页面访问...', 'info');

        const urls = ['/', '/trading-management', '/dashboard'];

        for (const url of urls) {
            setCurrentTest(url);
            try {
                const response = await fetch(url, { method: 'HEAD' });
                if (response.status === 200) {
                    addLog(`✅ ${url} - 可访问`, 'success');
                } else {
                    addLog(`❌ ${url} - 状态: ${response.status}`, 'error');
                }
            } catch (error) {
                addLog(`❌ ${url} - 错误: ${error instanceof Error ? error.message : '未知错误'}`, 'error');
            }
        }
        setCurrentTest('');
    };

    const testResources = async () => {
        addLog('开始测试静态资源...', 'info');

        const resources = ['/assets/index.js', '/assets/index.css'];

        for (const resource of resources) {
            setCurrentTest(resource);
            try {
                const response = await fetch(resource, { method: 'HEAD' });
                if (response.ok) {
                    addLog(`✅ ${resource} - 可用`, 'success');
                } else {
                    addLog(`❌ ${resource} - 不可用 (${response.status})`, 'error');
                }
            } catch (error) {
                addLog(`❌ ${resource} - 失败: ${error instanceof Error ? error.message : '未知错误'}`, 'error');
            }
        }
        setCurrentTest('');
    };

    const runAllTests = async () => {
        setIsRunning(true);
        clearLog();
        addLog('=== 开始综合诊断 ===', 'info');

        try {
            await testAPI();
            addLog('---', 'info');
            await testPages();
            addLog('---', 'info');
            await testResources();

            addLog('=== 诊断完成 ===', 'success');
        } catch (error) {
            addLog(`诊断过程出错: ${error instanceof Error ? error.message : '未知错误'}`, 'error');
        } finally {
            setIsRunning(false);
            setCurrentTest('');
        }
    };

    const testQuickLinks = [
        {
            name: 'API连接测试',
            icon: <ApiOutlined />,
            onClick: testAPI,
            description: '测试交易管理API的连通性'
        },
        {
            name: '页面访问测试',
            icon: <GlobalOutlined />,
            onClick: testPages,
            description: '测试主要页面的可访问性'
        },
        {
            name: '静态资源测试',
            icon: <FileTextOutlined />,
            onClick: testResources,
            description: '测试前端静态文件的加载'
        }
    ];

    const getProgressStatus = () => {
        if (!isRunning) return 'normal';
        return 'active';
    };

    return (
        <div style={{ padding: 24 }}>
            <Row gutter={24}>
                <Col span={24}>
                    <Card>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                            <div>
                                <Title level={2} style={{ margin: 0 }}>
                                    <ExperimentOutlined /> 系统诊断工具
                                </Title>
                                <Paragraph type="secondary">
                                    全面检测系统各个组件的运行状态
                                </Paragraph>
                            </div>
                            {isRunning && (
                                <div style={{ textAlign: 'center' }}>
                                    <Progress
                                        type="circle"
                                        percent={100}
                                        status={getProgressStatus()}
                                        size={60}
                                        format={() => '运行中'}
                                    />
                                    {currentTest && (
                                        <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                                            正在测试: {currentTest}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        <Space size="middle" style={{ marginBottom: 24 }}>
                            <Button
                                type="primary"
                                icon={<PlayCircleOutlined />}
                                onClick={runAllTests}
                                loading={isRunning}
                                size="large"
                            >
                                运行所有测试
                            </Button>
                            <Button
                                icon={<ClearOutlined />}
                                onClick={clearLog}
                                disabled={isRunning}
                            >
                                清空日志
                            </Button>
                        </Space>

                        {!isRunning && logs.length === 0 && (
                            <Alert
                                message="准备就绪"
                                description="点击'运行所有测试'开始系统诊断..."
                                type="info"
                                showIcon
                            />
                        )}
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={12}>
                    <Card title="快速测试">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            {testQuickLinks.map((test, index) => (
                                <Card
                                    key={index}
                                    size="small"
                                    hoverable
                                    style={{ cursor: 'pointer' }}
                                    onClick={isRunning ? undefined : test.onClick}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center' }}>
                                        <div style={{ marginRight: 12, fontSize: '18px', color: '#1890ff' }}>
                                            {test.icon}
                                        </div>
                                        <div>
                                            <div style={{ fontWeight: 'bold' }}>{test.name}</div>
                                            <div style={{ fontSize: '12px', color: '#666' }}>{test.description}</div>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </Space>

                        <Alert
                            message="快速测试"
                            description="点击上方卡片可以单独运行特定的测试项目"
                            type="info"
                            showIcon
                            style={{ marginTop: 16 }}
                        />
                    </Card>
                </Col>

                <Col span={12}>
                    <Card title="实时日志">
                        <div
                            ref={logsRef}
                            style={{
                                height: '350px',
                                overflowY: 'auto',
                                border: '1px solid #f0f0f0',
                                borderRadius: '4px',
                                padding: '12px',
                                backgroundColor: '#fafafa',
                                fontFamily: 'monospace',
                                fontSize: '12px'
                            }}
                        >
                            {logs.length === 0 ? (
                                <div style={{ textAlign: 'center', color: '#999', marginTop: 50 }}>
                                    点击按钮开始测试...
                                </div>
                            ) : (
                                logs.map((log, index) => (
                                    <div key={index} dangerouslySetInnerHTML={{ __html: log }} />
                                ))
                            )}
                        </div>
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={24}>
                    <Card title="系统信息">
                        <Row gutter={16}>
                            <Col span={8}>
                                <div>
                                    <Text strong>浏览器: </Text>
                                    <Text code>{navigator.userAgent.split(' ')[0]}</Text>
                                </div>
                                <div style={{ marginTop: 8 }}>
                                    <Text strong>当前时间: </Text>
                                    <Text>{new Date().toLocaleString()}</Text>
                                </div>
                            </Col>
                            <Col span={8}>
                                <div>
                                    <Text strong>当前地址: </Text>
                                    <Text code>{window.location.origin}</Text>
                                </div>
                                <div style={{ marginTop: 8 }}>
                                    <Text strong>页面路径: </Text>
                                    <Text code>{window.location.pathname}</Text>
                                </div>
                            </Col>
                            <Col span={8}>
                                <div>
                                    <Text strong>屏幕分辨率: </Text>
                                    <Text>{screen.width} x {screen.height}</Text>
                                </div>
                                <div style={{ marginTop: 8 }}>
                                    <Text strong>视口大小: </Text>
                                    <Text>{window.innerWidth} x {window.innerHeight}</Text>
                                </div>
                            </Col>
                        </Row>

                        <Alert
                            message="诊断说明"
                            description={
                                <ul style={{ margin: 0, paddingLeft: 20 }}>
                                    <li><strong>API连接测试</strong>: 检查后端API服务的可用性和响应</li>
                                    <li><strong>页面访问测试</strong>: 验证前端路由和页面渲染是否正常</li>
                                    <li><strong>静态资源测试</strong>: 确认JavaScript、CSS等资源文件加载正常</li>
                                    <li><strong>综合诊断</strong>: 一次性运行所有测试，全面检查系统状态</li>
                                </ul>
                            }
                            type="info"
                            showIcon
                            style={{ marginTop: 16 }}
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default SystemDiagnostic; 