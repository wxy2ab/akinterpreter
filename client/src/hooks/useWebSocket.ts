import { useCallback, useEffect, useRef, useState } from 'react';

interface WebSocketHook {
    connected: boolean;
    isConnected: boolean;
    connect: () => void;
    disconnect: () => void;
    subscribe: (eventTypes: string[], handler: (data: any) => void) => void;
    unsubscribe: (eventTypes: string[]) => void;
    sendMessage: (message: any) => boolean;
    lastMessage: any;
}

interface EventHandler {
    eventTypes: string[];
    handler: (data: any) => void;
}

export const useWebSocket = (): WebSocketHook => {
    const [connected, setConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<any>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const eventHandlersRef = useRef<EventHandler[]>([]);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const isConnectingRef = useRef(false);

    const connect = useCallback(() => {
        if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket已在连接中，跳过...');
            return;
        }

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log('WebSocket已连接，跳过...');
            return;
        }

        isConnectingRef.current = true;

        // 构建WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        console.log('连接WebSocket:', wsUrl);

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('WebSocket连接成功');
                isConnectingRef.current = false;
                reconnectAttemptsRef.current = 0;
                setConnected(true);

                // 发送初始订阅消息
                const subscribeMessage = {
                    type: 'subscribe',
                    event_types: ['*'] // 订阅所有事件
                };

                ws.send(JSON.stringify(subscribeMessage));
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                } catch (error) {
                    console.error('解析WebSocket消息失败:', error);
                }
            };

            ws.onclose = (event) => {
                console.log('WebSocket连接断开:', event.code, event.reason);
                isConnectingRef.current = false;
                setConnected(false);

                // 自动重连逻辑
                if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
                    reconnectAttemptsRef.current++;

                    console.log(`${delay / 1000}秒后尝试重连 (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

                    if (reconnectTimeoutRef.current) {
                        clearTimeout(reconnectTimeoutRef.current);
                    }

                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, delay);
                } else {
                    console.log('达到最大重连次数');
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                isConnectingRef.current = false;
            };

        } catch (error) {
            console.error('创建WebSocket连接失败:', error);
            isConnectingRef.current = false;
        }
    }, []);

    const disconnect = useCallback(() => {
        console.log('手动断开WebSocket连接');

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (wsRef.current) {
            wsRef.current.close(1000, '手动断开');
            wsRef.current = null;
        }

        setConnected(false);
        reconnectAttemptsRef.current = maxReconnectAttempts; // 阻止自动重连
    }, []);

    const handleMessage = useCallback((data: any) => {
        // 更新最后一条消息
        setLastMessage(data);

        // 分发消息给所有相关的事件处理器
        eventHandlersRef.current.forEach(({ eventTypes, handler }) => {
            // 检查是否匹配事件类型
            const isMatch = eventTypes.includes('*') ||
                eventTypes.includes(data.type) ||
                (data.event_type && eventTypes.includes(data.event_type));

            if (isMatch) {
                try {
                    handler(data);
                } catch (error) {
                    console.error('事件处理器执行失败:', error);
                }
            }
        });
    }, []);

    const subscribe = useCallback((eventTypes: string[], handler: (data: any) => void) => {
        const eventHandler: EventHandler = { eventTypes, handler };
        eventHandlersRef.current.push(eventHandler);

        console.log('订阅事件:', eventTypes);
    }, []);

    const unsubscribe = useCallback((eventTypes: string[]) => {
        eventHandlersRef.current = eventHandlersRef.current.filter(
            ({ eventTypes: handlerEventTypes }) => {
                // 如果事件类型有重叠，则移除
                return !eventTypes.some(type => handlerEventTypes.includes(type));
            }
        );

        console.log('取消订阅事件:', eventTypes);
    }, []);

    const sendMessage = useCallback((message: any): boolean => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log('发送WebSocket消息:', message);
            wsRef.current.send(JSON.stringify(message));
            return true;
        } else {
            console.warn('WebSocket未连接，无法发送消息');
            return false;
        }
    }, []);

    // 自动连接
    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [connect]);

    return {
        connected,
        isConnected: connected,
        connect,
        disconnect,
        subscribe,
        unsubscribe,
        sendMessage,
        lastMessage
    };
}; 