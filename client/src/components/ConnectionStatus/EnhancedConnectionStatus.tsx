import { CheckCircleOutlined, CloseCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { Badge, Space, Tooltip, Typography } from 'antd';
import React from 'react';

const { Text } = Typography;

interface ConnectionStatusProps {
    status?: any;
    compact?: boolean;
    simple?: boolean;
    detailed?: boolean;
    analysis?: any;
    displayStatus?: any;
    showDetails?: boolean;
}

const EnhancedConnectionStatus: React.FC<ConnectionStatusProps> = ({
    status,
    compact = false,
    simple = false,
    detailed = false
}) => {
    // 如果没有状态数据，显示默认信息
    if (!status) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <QuestionCircleOutlined style={{ color: '#faad14' }} />
                <Text type="secondary">CTP服务未启动</Text>
            </div>
        );
    }

    // 提取状态信息
    const {
        ctp_kernel_running = false,
        trade_server_connected = false,
        quote_server_connected = false,
        display_status = "未知",
        status_details = {}
    } = status;

    // 如果没有这些新字段，回退到旧字段
    const kernelRunning = ctp_kernel_running !== undefined ? ctp_kernel_running : status.ctp_connected;
    const tradeConnected = trade_server_connected;
    const quoteConnected = quote_server_connected;

    // 状态图标和颜色
    const getStatusIcon = (isConnected: boolean) => {
        if (isConnected) {
            return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
        } else {
            return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
        }
    };

    const getStatusColor = (isConnected: boolean) => {
        return isConnected ? '#52c41a' : '#ff4d4f';
    };

    // 紧凑模式 - 只显示主要状态
    if (compact) {
        const overallStatus = kernelRunning ? '已启动' : '未启动';
        const statusColor = kernelRunning ? '#52c41a' : '#ff4d4f';
        const statusIcon = kernelRunning ? <CheckCircleOutlined /> : <CloseCircleOutlined />;

        return (
            <Tooltip title={`CTP内核: ${kernelRunning ? '运行中' : '未运行'}, 交易服务器: ${tradeConnected ? '已连接' : '未连接'}, 行情服务器: ${quoteConnected ? '已连接' : '未连接'}`}>
                <Badge
                    status={kernelRunning ? 'success' : 'error'}
                    text={
                        <span style={{ color: statusColor }}>
                            {statusIcon} CTP {overallStatus}
                        </span>
                    }
                />
            </Tooltip>
        );
    }

    // 简单模式 - 显示主要状态和简要信息
    if (simple) {
        return (
            <Space direction="vertical" size="small">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getStatusIcon(kernelRunning)}
                    <Text strong>CTP内核: {kernelRunning ? '运行中' : '未运行'}</Text>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getStatusIcon(tradeConnected)}
                    <Text>交易服务器: {tradeConnected ? '已连接' : '未连接'}</Text>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getStatusIcon(quoteConnected)}
                    <Text>行情服务器: {quoteConnected ? '已连接' : '未连接'}</Text>
                </div>
            </Space>
        );
    }

    // 详细模式 - 显示完整状态信息
    if (detailed) {
        return (
            <div style={{ padding: '12px', border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fafafa' }}>
                <Typography.Title level={5} style={{ marginBottom: '12px' }}>
                    CTP连接状态详情
                </Typography.Title>

                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {/* CTP内核状态 */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text strong>CTP交易内核:</Text>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {getStatusIcon(kernelRunning)}
                            <Text style={{ color: getStatusColor(kernelRunning) }}>
                                {kernelRunning ? '运行中' : '未运行'}
                            </Text>
                        </div>
                    </div>

                    {/* 交易服务器状态 */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text>交易服务器:</Text>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {getStatusIcon(tradeConnected)}
                            <Text style={{ color: getStatusColor(tradeConnected) }}>
                                {tradeConnected ? '已连接' : '未连接'}
                            </Text>
                        </div>
                    </div>

                    {/* 行情服务器状态 */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text>行情服务器:</Text>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {getStatusIcon(quoteConnected)}
                            <Text style={{ color: getStatusColor(quoteConnected) }}>
                                {quoteConnected ? '已连接' : '未连接'}
                            </Text>
                        </div>
                    </div>

                    {/* 状态描述 */}
                    {status_details.description && (
                        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                {status_details.description}
                            </Text>
                        </div>
                    )}
                </Space>
            </div>
        );
    }

    // 默认模式 - 显示综合状态
    const overallStatus = kernelRunning ? '已启动' : '未启动';
    const statusColor = kernelRunning ? '#52c41a' : '#ff4d4f';
    const statusIcon = kernelRunning ? <CheckCircleOutlined /> : <CloseCircleOutlined />;

    return (
        <Tooltip title={`CTP内核: ${kernelRunning ? '运行中' : '未运行'}, 交易服务器: ${tradeConnected ? '已连接' : '未连接'}, 行情服务器: ${quoteConnected ? '已连接' : '未连接'}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {statusIcon}
                <Text style={{ color: statusColor, fontWeight: 'bold' }}>
                    CTP {overallStatus}
                </Text>
                {kernelRunning && (
                    <div style={{ display: 'flex', gap: '4px' }}>
                        <Badge
                            size="small"
                            status={tradeConnected ? 'success' : 'error'}
                            text="T"
                        />
                        <Badge
                            size="small"
                            status={quoteConnected ? 'success' : 'error'}
                            text="Q"
                        />
                    </div>
                )}
            </div>
        </Tooltip>
    );
};

export default EnhancedConnectionStatus; 