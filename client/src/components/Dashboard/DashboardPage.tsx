import { Card, Col, Row, Statistic, Typography } from 'antd';
import React from 'react';
import { useSelector } from 'react-redux';

import { useSystemStatus } from '../../hooks/useSystemStatus';
import { RootState } from '../../store/store';
import EnhancedConnectionStatus from '../ConnectionStatus/EnhancedConnectionStatus';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
    const systemStatus = useSelector((state: RootState) => state.system.status);
    const isConnected = useSelector((state: RootState) => state.system.connected);

    // 使用系统状态hook来定期更新状态
    useSystemStatus();

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>交易系统仪表板</Title>

            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="CTP连接状态"
                            value={systemStatus?.ctp_connected ? "已连接" : "未连接"}
                            valueStyle={{
                                color: systemStatus?.ctp_connected ? '#3f8600' : '#cf1322'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="WebSocket状态"
                            value={isConnected ? "已连接" : "断开"}
                            valueStyle={{
                                color: isConnected ? '#3f8600' : '#cf1322'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="活跃连接数"
                            value={systemStatus?.active_connections || 0}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="交易日"
                            value={systemStatus?.trading_day || "未知"}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 🔧 增强：详细连接状态显示 */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={24}>
                    <EnhancedConnectionStatus
                        status={systemStatus}
                        analysis={systemStatus?.ctp_status_analysis}
                        displayStatus={systemStatus?.display_status}
                        showDetails={false}
                    />
                </Col>
            </Row>

            <Row gutter={16}>
                <Col span={12}>
                    <Card title="系统信息" style={{ height: 300 }}>
                        <p><strong>服务器时间:</strong> {systemStatus?.server_time ? new Date(systemStatus.server_time).toLocaleString() : "未知"}</p>
                        <p><strong>CTP运行状态:</strong> {systemStatus?.ctp_connected ? "运行中" : "停止"}</p>
                        <p><strong>Web桥接状态:</strong> {systemStatus?.web_bridge_running ? "运行中" : "停止"}</p>
                        <p><strong>当前用户:</strong> {localStorage.getItem('currentUser') || "未知"}</p>
                        <p><strong>活跃连接数:</strong> {systemStatus?.active_connections || 0}</p>
                        {systemStatus?.web_bridge_details && (
                            <p><strong>事件处理数:</strong> {systemStatus.web_bridge_details.events_processed || 0}</p>
                        )}
                    </Card>
                </Col>
                <Col span={12}>
                    <Card title="快速操作" style={{ height: 300 }}>
                        <p>• 查看实时行情</p>
                        <p>• 手动下单</p>
                        <p>• 查看持仓</p>
                        <p>• 系统设置</p>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default DashboardPage; 