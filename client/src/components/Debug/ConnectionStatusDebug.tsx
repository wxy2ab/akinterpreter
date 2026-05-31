import { Card, Typography } from 'antd';
import React from 'react';
import { useSelector } from 'react-redux';

import { RootState } from '../../store/store';

const { Text } = Typography;

const ConnectionStatusDebug: React.FC = () => {
    const systemStatus = useSelector((state: RootState) => state.system.status);

    return (
        <Card title="连接状态调试" size="small">
            <div>
                <Text strong>系统状态数据:</Text>
                <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                    {JSON.stringify(systemStatus, null, 2)}
                </pre>
            </div>

            <div style={{ marginTop: 16 }}>
                <Text strong>关键字段:</Text>
                <ul>
                    <li>ctp_connected: {systemStatus?.ctp_connected?.toString()}</li>
                    <li>display_status: {systemStatus?.display_status ? '存在' : '不存在'}</li>
                    <li>ctp_status_analysis: {systemStatus?.ctp_status_analysis ? '存在' : '不存在'}</li>
                </ul>
            </div>

            {systemStatus?.display_status && (
                <div style={{ marginTop: 16 }}>
                    <Text strong>显示状态:</Text>
                    <ul>
                        <li>状态描述: {systemStatus.display_status.status_description}</li>
                        <li>状态级别: {systemStatus.display_status.status_level}</li>
                        <li>是否交易时间: {systemStatus.display_status.is_trading_time?.toString()}</li>
                    </ul>
                </div>
            )}
        </Card>
    );
};

export default ConnectionStatusDebug; 