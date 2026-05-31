import { Alert, Button, Card, Spin, Typography } from 'antd';
import React, { useEffect, useState } from 'react';

const { Title, Text } = Typography;

interface DebugInfo {
    timestamp: string;
    error?: string;
    apiStatus: {
        positions?: string;
        orders?: string;
        account?: string;
        status?: string;
    };
}

const TradingPanelDebug: React.FC = () => {
    const [debugInfo, setDebugInfo] = useState<DebugInfo>({
        timestamp: new Date().toLocaleString(),
        apiStatus: {}
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        console.log('TradingPanelDebug组件已挂载');
        testAPIs();

        return () => {
            console.log('TradingPanelDebug组件已卸载');
        };
    }, []);

    const testAPI = async (url: string, name: string) => {
        try {
            console.log(`测试API: ${name} - ${url}`);
            const response = await fetch(url);
            const result = `${response.status} ${response.statusText}`;
            console.log(`API ${name} 响应:`, result);

            if (response.ok) {
                const data = await response.json();
                console.log(`API ${name} 数据:`, data);
            }

            return result;
        } catch (error) {
            console.error(`API ${name} 错误:`, error);
            return `错误: ${error instanceof Error ? error.message : String(error)}`;
        }
    };

    const testAPIs = async () => {
        setLoading(true);
        try {
            const [positions, orders, account, status] = await Promise.all([
                testAPI('/api/trading-management/positions', 'positions'),
                testAPI('/api/trading-management/orders', 'orders'),
                testAPI('/api/trading-management/account', 'account'),
                testAPI('/api/trading-management/status', 'status')
            ]);

            setDebugInfo(prev => ({
                ...prev,
                timestamp: new Date().toLocaleString(),
                apiStatus: { positions, orders, account, status }
            }));
        } catch (error) {
            console.error('测试API失败:', error);
            setDebugInfo(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : String(error),
                timestamp: new Date().toLocaleString()
            }));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <Title level={2}>🔧 交易管理页面 - 诊断模式</Title>

            <Alert
                message="诊断模式已激活"
                description="这是一个简化的诊断组件，用于调试白屏问题。请检查浏览器控制台以获取详细信息。"
                type="info"
                style={{ marginBottom: '20px' }}
            />

            <Card title="组件状态" style={{ marginBottom: '20px' }}>
                <p><Text strong>组件挂载时间:</Text> {debugInfo.timestamp}</p>
                <p><Text strong>加载状态:</Text> {loading ? '测试中...' : '已完成'}</p>
                {debugInfo.error && (
                    <Alert message="组件错误" description={debugInfo.error} type="error" />
                )}
            </Card>

            <Card
                title="API端点测试"
                style={{ marginBottom: '20px' }}
                extra={
                    <Button onClick={testAPIs} loading={loading}>
                        重新测试
                    </Button>
                }
            >
                {loading ? (
                    <Spin tip="测试API端点..." />
                ) : (
                    <div>
                        <p><Text strong>持仓API:</Text> {debugInfo.apiStatus.positions || '未测试'}</p>
                        <p><Text strong>订单API:</Text> {debugInfo.apiStatus.orders || '未测试'}</p>
                        <p><Text strong>账户API:</Text> {debugInfo.apiStatus.account || '未测试'}</p>
                        <p><Text strong>状态API:</Text> {debugInfo.apiStatus.status || '未测试'}</p>
                    </div>
                )}
            </Card>

            <Card title="浏览器信息">
                <p><Text strong>User Agent:</Text> {navigator.userAgent}</p>
                <p><Text strong>当前URL:</Text> {window.location.href}</p>
                <p><Text strong>React环境:</Text> {process.env.NODE_ENV}</p>
            </Card>

            <Alert
                message="诊断指南"
                description={
                    <div>
                        <p>1. 检查浏览器控制台是否有错误信息</p>
                        <p>2. 查看API测试结果，确认后端服务是否正常</p>
                        <p>3. 如果所有API都返回200，说明后端正常，问题在前端组件</p>
                        <p>4. 如果API返回错误，需要检查后端服务</p>
                    </div>
                }
                type="warning"
                style={{ marginTop: '20px' }}
            />
        </div>
    );
};

export default TradingPanelDebug; 