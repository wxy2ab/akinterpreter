import { Card, Col, Row, Typography } from 'antd';
import React from 'react';

import EnhancedConnectionStatus from '../ConnectionStatus/EnhancedConnectionStatus';
import ConnectionStatusDebug from './ConnectionStatusDebug';

const { Title } = Typography;

const DebugPage: React.FC = () => {
    return (
        <div>
            <Title level={2}>调试页面</Title>

            <Row gutter={16}>
                <Col span={12}>
                    <Card title="连接状态调试" style={{ marginBottom: 16 }}>
                        <ConnectionStatusDebug />
                    </Card>
                </Col>

                <Col span={12}>
                    <Card title="增强连接状态组件" style={{ marginBottom: 16 }}>
                        <EnhancedConnectionStatus status={null} showDetails={true} />
                    </Card>
                </Col>
            </Row>

            <Row gutter={16}>
                <Col span={24}>
                    <Card title="紧凑模式连接状态">
                        <EnhancedConnectionStatus status={null} compact={true} />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default DebugPage; 