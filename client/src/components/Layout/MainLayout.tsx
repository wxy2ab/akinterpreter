import {
    BugOutlined,
    DashboardOutlined,
    FundOutlined,
    LineChartOutlined,
    LogoutOutlined,
    SettingOutlined,
    TransactionOutlined,
    UserOutlined
} from '@ant-design/icons';
import { Badge, Button, Dropdown, Layout, Menu, Space, Typography } from 'antd';
import React from 'react';
import { useSelector } from 'react-redux';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';

import { useWebSocket } from '../../context/WebSocketContext';
import { RootState } from '../../store/store';
import EnhancedConnectionStatus from '../ConnectionStatus/EnhancedConnectionStatus';
import DashboardPage from '../Dashboard/DashboardPage';
import DebugPage from '../Debug/DebugPage';
import SimpleTest from '../Debug/SimpleTest';
import SystemDiagnostic from '../Debug/SystemDiagnostic';
import TradingApiDebug from '../Debug/TradingApiDebug';
import WebSocketTest from '../Debug/WebSocketTest';
import MarketWatchPage from '../MarketWatch/MarketWatchPage';
import SettingsPage from '../Settings/SettingsPage';
import StrategyPage from '../Strategy/StrategyPage';
import TradingPage from '../Trading/TradingPage';
import TradingPanel from '../Trading/TradingPanel';
import TradingPanelOptimized from '../Trading/TradingPanelOptimized';
// import TradingPanelDebug from '../Trading/TradingPanelDebug';  // 保留用于调试

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

interface MainLayoutProps {
    onLogout?: () => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ onLogout }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { isConnected } = useWebSocket();

    const systemConnected = useSelector((state: RootState) => state.system.connected);
    const ctpRunning = useSelector((state: RootState) => state.system.status?.ctp_connected);
    const systemStatus = useSelector((state: RootState) => state.system.status);

    const currentUser = localStorage.getItem('currentUser') || '用户';

    const menuItems = [
        {
            key: '/dashboard',
            icon: <DashboardOutlined />,
            label: '仪表板',
        },
        {
            key: '/market',
            icon: <LineChartOutlined />,
            label: '行情',
        },
        {
            key: '/trading',
            icon: <TransactionOutlined />,
            label: '交易',
        },
        {
            key: '/trading-management',
            icon: <TransactionOutlined />,
            label: '交易管理',
        },
        {
            key: '/strategy',
            icon: <FundOutlined />,
            label: '策略',
        },
        {
            key: '/settings',
            icon: <SettingOutlined />,
            label: '设置',
        },
        {
            key: '/debug',
            icon: <BugOutlined />,
            label: '调试',
            children: [
                {
                    key: '/debug-trading-api',
                    label: 'API诊断',
                },
                {
                    key: '/ws-test',
                    label: 'WebSocket测试',
                },
                {
                    key: '/system-diagnostic',
                    label: '系统诊断',
                },
                {
                    key: '/test-simple',
                    label: '简单测试',
                },
            ]
        },
    ];

    const handleMenuClick = (e: any) => {
        navigate(e.key);
    };

    const handleLogout = async () => {
        try {
            // 停止CTP服务
            await fetch('/api/system/stop-ctp', { method: 'POST' });
        } catch (error) {
            console.error('停止CTP服务失败:', error);
        }

        // 调用父组件的logout回调
        if (onLogout) {
            onLogout();
        }
    };

    const userMenuItems = [
        {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: '退出登录',
            onClick: handleLogout,
        },
    ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Header style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: '#001529',
                padding: '0 24px'
            }}>
                <Title level={3} style={{ color: 'white', margin: 0 }}>
                    CTP Web Trading System
                </Title>

                <Space>
                    <Dropdown
                        menu={{ items: userMenuItems }}
                        placement="bottomRight"
                        trigger={['click']}
                    >
                        <Button
                            type="text"
                            style={{ color: 'white' }}
                            icon={<UserOutlined />}
                        >
                            {currentUser}
                        </Button>
                    </Dropdown>

                    {/* WebSocket连接状态 */}
                    <Badge
                        status={isConnected ? 'success' : 'error'}
                        text={isConnected ? 'WebSocket已连接' : 'WebSocket断开'}
                        style={{ color: 'white' }}
                    />

                    {/* 🔧 增强：CTP详细连接状态 */}
                    <EnhancedConnectionStatus
                        status={systemStatus}
                        analysis={systemStatus?.ctp_status_analysis}
                        displayStatus={systemStatus?.display_status}
                        compact={true}
                    />
                </Space>
            </Header>

            <Layout>
                <Sider width={200} style={{ background: '#fff' }}>
                    <Menu
                        mode="inline"
                        selectedKeys={[location.pathname]}
                        style={{ height: '100%', borderRight: 0 }}
                        items={menuItems}
                        onClick={handleMenuClick}
                    />
                </Sider>

                <Layout style={{ padding: '0 24px 24px' }}>
                    <Content
                        style={{
                            background: '#fff',
                            padding: 24,
                            margin: 0,
                            minHeight: 280,
                        }}
                    >
                        <Routes>
                            <Route path="/dashboard" element={<DashboardPage />} />
                            <Route path="/market" element={<MarketWatchPage />} />
                            <Route path="/trading" element={<TradingPage />} />
                            <Route path="/trading-management" element={<TradingPanel />} />
                            <Route path="/trading-management-optimized" element={<TradingPanelOptimized />} />
                            <Route path="/strategy" element={<StrategyPage />} />
                            <Route path="/settings" element={<SettingsPage />} />
                            <Route path="/debug" element={<DebugPage />} />
                            <Route path="/debug-trading-api" element={<TradingApiDebug />} />
                            <Route path="/ws-test" element={<WebSocketTest />} />
                            <Route path="/system-diagnostic" element={<SystemDiagnostic />} />
                            <Route path="/test-simple" element={<SimpleTest />} />
                            <Route path="/" element={<DashboardPage />} />
                        </Routes>
                    </Content>
                </Layout>
            </Layout>
        </Layout>
    );
};

export default MainLayout; 