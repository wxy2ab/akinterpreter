import {
    ClearOutlined,
    DisconnectOutlined,
    PlayCircleOutlined,
    SendOutlined,
    WifiOutlined
} from '@ant-design/icons';
import { Alert, Button, Card, Col, Input, Row, Space, Tag, Typography } from 'antd';
import React, { useEffect, useRef, useState } from 'react';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface WebSocketMessage {
    id: string;
    timestamp: string;
    type: 'sent' | 'received' | 'system';
    content: string;
    data?: any;
}

const WebSocketTest: React.FC = () => {
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
    const [messages, setMessages] = useState<WebSocketMessage[]>([]);
    const [customMessage, setCustomMessage] = useState('{"type": "test", "message": "Hello WebSocket!"}');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const addMessage = (type: WebSocketMessage['type'], content: string, data?: any) => {
        const message: WebSocketMessage = {
            id: Date.now().toString(),
            timestamp: new Date().toLocaleTimeString(),
            type,
            content,
            data
        };
        setMessages(prev => [...prev, message]);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const connect = () => {
        if (ws) {
            ws.close();
        }

        setConnectionStatus('connecting');
        addMessage('system', '正在连接WebSocket...');

        const websocket = new WebSocket(`ws://${window.location.host}/ws`);

        websocket.onopen = (event) => {
            setConnectionStatus('connected');
            addMessage('system', '✅ WebSocket连接已建立');
            setWs(websocket);
        };

        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                addMessage('received', `收到消息`, data);
            } catch (error) {
                addMessage('received', `收到消息: ${event.data}`);
            }
        };

        websocket.onclose = (event) => {
            setConnectionStatus('disconnected');
            addMessage('system', `❌ WebSocket连接已断开 (代码: ${event.code})`);
            setWs(null);
        };

        websocket.onerror = (error) => {
            addMessage('system', `❌ WebSocket连接错误: ${error}`);
        };
    };

    const disconnect = () => {
        if (ws) {
            ws.close();
            addMessage('system', '主动断开WebSocket连接');
        }
    };

    const sendMessage = (message?: string) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            addMessage('system', '❌ WebSocket未连接');
            return;
        }

        const messageToSend = message || customMessage;
        try {
            ws.send(messageToSend);
            addMessage('sent', `发送消息`, JSON.parse(messageToSend));
        } catch (error) {
            addMessage('system', `❌ 发送消息失败: ${error}`);
        }
    };

    const sendSubscription = () => {
        const subscribeMessage = JSON.stringify({
            type: "subscribe",
            event_types: ["*"]
        });
        sendMessage(subscribeMessage);
    };

    const clearMessages = () => {
        setMessages([]);
    };

    const getStatusColor = () => {
        switch (connectionStatus) {
            case 'connected': return 'success';
            case 'connecting': return 'processing';
            case 'disconnected': return 'default';
        }
    };

    const getStatusText = () => {
        switch (connectionStatus) {
            case 'connected': return '已连接';
            case 'connecting': return '连接中...';
            case 'disconnected': return '未连接';
        }
    };

    const renderMessage = (message: WebSocketMessage) => {
        const getMessageStyle = () => {
            switch (message.type) {
                case 'sent':
                    return {
                        background: '#e6f7ff',
                        borderLeft: '3px solid #1890ff',
                        marginLeft: '20px'
                    };
                case 'received':
                    return {
                        background: '#f6ffed',
                        borderLeft: '3px solid #52c41a',
                        marginRight: '20px'
                    };
                case 'system':
                    return {
                        background: '#fff7e6',
                        borderLeft: '3px solid #fa8c16'
                    };
            }
        };

        return (
            <div
                key={message.id}
                style={{
                    ...getMessageStyle(),
                    padding: '12px',
                    margin: '8px 0',
                    borderRadius: '4px',
                    fontSize: '14px'
                }}
            >
                <div style={{ marginBottom: '4px' }}>
                    <Space>
                        <Tag color={message.type === 'sent' ? 'blue' : message.type === 'received' ? 'green' : 'orange'}>
                            {message.type === 'sent' ? '发送' : message.type === 'received' ? '接收' : '系统'}
                        </Tag>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                            {message.timestamp}
                        </Text>
                    </Space>
                </div>
                <div>{message.content}</div>
                {message.data && (
                    <pre style={{
                        marginTop: '8px',
                        background: 'rgba(0,0,0,0.05)',
                        padding: '8px',
                        borderRadius: '4px',
                        fontSize: '12px'
                    }}>
                        {JSON.stringify(message.data, null, 2)}
                    </pre>
                )}
            </div>
        );
    };

    return (
        <div style={{ padding: 24 }}>
            <Row gutter={24}>
                <Col span={24}>
                    <Card>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                            <div>
                                <Title level={2} style={{ margin: 0 }}>
                                    <WifiOutlined /> WebSocket连接测试
                                </Title>
                                <Paragraph type="secondary">
                                    测试WebSocket实时通信功能
                                </Paragraph>
                            </div>
                            <Tag color={getStatusColor()} style={{ fontSize: '14px' }}>
                                {getStatusText()}
                            </Tag>
                        </div>

                        <Space size="middle" style={{ marginBottom: 24 }}>
                            <Button
                                type="primary"
                                icon={<WifiOutlined />}
                                onClick={connect}
                                disabled={connectionStatus === 'connecting'}
                                loading={connectionStatus === 'connecting'}
                            >
                                连接WebSocket
                            </Button>
                            <Button
                                icon={<DisconnectOutlined />}
                                onClick={disconnect}
                                disabled={connectionStatus === 'disconnected'}
                            >
                                断开连接
                            </Button>
                            <Button
                                icon={<PlayCircleOutlined />}
                                onClick={sendSubscription}
                                disabled={connectionStatus !== 'connected'}
                            >
                                订阅行情
                            </Button>
                            <Button
                                icon={<ClearOutlined />}
                                onClick={clearMessages}
                            >
                                清空消息
                            </Button>
                        </Space>

                        {connectionStatus === 'disconnected' && (
                            <Alert
                                message="WebSocket未连接"
                                description="点击'连接WebSocket'开始测试实时通信功能"
                                type="info"
                                showIcon
                                style={{ marginBottom: 16 }}
                            />
                        )}
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={12}>
                    <Card title="发送自定义消息">
                        <Space.Compact style={{ display: 'flex', marginBottom: 16 }}>
                            <TextArea
                                value={customMessage}
                                onChange={(e) => setCustomMessage(e.target.value)}
                                placeholder="输入JSON格式的消息"
                                rows={4}
                                style={{ flex: 1 }}
                            />
                        </Space.Compact>
                        <Button
                            type="primary"
                            icon={<SendOutlined />}
                            onClick={() => sendMessage()}
                            disabled={connectionStatus !== 'connected'}
                            block
                        >
                            发送消息
                        </Button>

                        <div style={{ marginTop: 16 }}>
                            <Text strong>快速发送:</Text>
                            <div style={{ marginTop: 8 }}>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <Button
                                        size="small"
                                        block
                                        onClick={() => sendMessage('{"type": "ping"}')}
                                        disabled={connectionStatus !== 'connected'}
                                    >
                                        Ping消息
                                    </Button>
                                    <Button
                                        size="small"
                                        block
                                        onClick={() => sendMessage('{"type": "market_data_request", "symbol": "rb2507"}')}
                                        disabled={connectionStatus !== 'connected'}
                                    >
                                        请求行情数据
                                    </Button>
                                    <Button
                                        size="small"
                                        block
                                        onClick={() => sendMessage('{"type": "position_update_request"}')}
                                        disabled={connectionStatus !== 'connected'}
                                    >
                                        请求持仓更新
                                    </Button>
                                </Space>
                            </div>
                        </div>
                    </Card>
                </Col>

                <Col span={12}>
                    <Card title="消息日志">
                        <div
                            style={{
                                height: '400px',
                                overflowY: 'auto',
                                border: '1px solid #f0f0f0',
                                borderRadius: '4px',
                                padding: '8px'
                            }}
                        >
                            {messages.length === 0 ? (
                                <div style={{ textAlign: 'center', color: '#999', marginTop: 50 }}>
                                    暂无消息记录
                                </div>
                            ) : (
                                messages.map(renderMessage)
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    </Card>
                </Col>
            </Row>

            <Row gutter={24} style={{ marginTop: 24 }}>
                <Col span={24}>
                    <Card title="WebSocket信息">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                                <Text strong>连接地址: </Text>
                                <Text code>{`ws://${window.location.host}/ws`}</Text>
                            </div>
                            <div>
                                <Text strong>连接状态: </Text>
                                <Tag color={getStatusColor()}>{getStatusText()}</Tag>
                            </div>
                            {ws && (
                                <>
                                    <div>
                                        <Text strong>就绪状态: </Text>
                                        <Text code>{ws.readyState}</Text>
                                    </div>
                                    <div>
                                        <Text strong>协议: </Text>
                                        <Text code>{ws.protocol || '无'}</Text>
                                    </div>
                                </>
                            )}
                            <Alert
                                message="使用说明"
                                description={
                                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                                        <li>点击"连接WebSocket"建立实时通信连接</li>
                                        <li>使用"订阅行情"接收实时市场数据推送</li>
                                        <li>在左侧输入框发送自定义JSON消息</li>
                                        <li>右侧消息日志显示所有发送和接收的消息</li>
                                    </ul>
                                }
                                type="info"
                                showIcon
                            />
                        </Space>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default WebSocketTest; 