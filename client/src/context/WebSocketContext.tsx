import { message } from 'antd';
import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useDispatch } from 'react-redux';

import { updateAccountInfo } from '../store/slices/accountSlice';
import { updateBasePrice, updateTick } from '../store/slices/marketSlice';
import { updateStrategy } from '../store/slices/strategySlice';
import { addLog, setConnected } from '../store/slices/systemSlice';
import { updateOrder, updatePosition, updateTrade } from '../store/slices/tradingSlice';

interface WebSocketContextType {
    isConnected: boolean;
    sendMessage: (message: any) => boolean;
    connect: () => void;
    disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
    const context = useContext(WebSocketContext);
    if (!context) {
        throw new Error('useWebSocket must be used within a WebSocketProvider');
    }
    return context;
};

interface WebSocketProviderProps {
    children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
    const dispatch = useDispatch();
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const isConnectingRef = useRef(false);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 10;
    const [isConnected, setIsConnected] = useState(false);

    const handleMessage = useCallback((data: any) => {
        const { type, event_type, data: eventData } = data;

        console.log('WebSocket message received:', { type, event_type, eventData });

        if (type === 'event') {
            switch (event_type) {
                case 'market_tick':
                case 'tick_update':
                case 'tick_data':
                    dispatch(updateTick(eventData));
                    break;

                case 'position_update':
                    dispatch(updatePosition(eventData));
                    break;

                case 'order_update':
                case 'order_placed':
                case 'order_filled':
                case 'order_cancelled':
                case 'order_rejected':
                    dispatch(updateOrder(eventData));
                    break;

                case 'trade_update':
                    dispatch(updateTrade(eventData));
                    break;

                case 'account_update':
                    dispatch(updateAccountInfo(eventData));
                    break;

                case 'strategy_update':
                case 'strategy_status_update':
                    dispatch(updateStrategy(eventData));
                    break;

                case 'system_log':
                    dispatch(addLog(`${eventData.timestamp || new Date().toLocaleTimeString()} [${eventData.level || 'INFO'}] ${eventData.message}`));
                    break;

                case 'risk_warning':
                    message.warning(`风控警告: ${eventData.message || '风控事件'}`);
                    dispatch(addLog(`风控警告: ${JSON.stringify(eventData)}`));
                    break;

                case 'error_occurred':
                    message.error(`系统错误: ${eventData.message || '未知错误'}`);
                    dispatch(addLog(`系统错误: ${JSON.stringify(eventData)}`));
                    break;

                case 'connection_status':
                    dispatch(addLog(`连接状态更新: ${JSON.stringify(eventData)}`));
                    break;

                default:
                    console.log('未处理的事件类型:', event_type, eventData);
                    dispatch(addLog(`未处理事件: ${event_type}`));
            }
        } else if (type === 'base_price_update') {
            // 处理基准价格更新事件
            const { symbol, base_price } = eventData;
            if (symbol && base_price > 1e-6) {
                console.log(`收到基准价格更新: ${symbol} = ${base_price}`);
                dispatch(updateBasePrice({ symbol, basePrice: base_price }));
                dispatch(addLog(`基准价格已更新: ${symbol} = ${base_price.toFixed(2)}`));
            }
        } else if (type === 'recalculate_prices') {
            // 处理重新计算价格事件
            console.log('收到重新计算价格请求');
            dispatch(addLog('正在重新计算涨跌和涨跌幅...'));
            // 这里可以触发前端重新获取数据或重新计算
        } else if (type === 'connection_established') {
            message.success('已连接到交易服务器');
            dispatch(addLog('已连接到交易服务器'));

            // 连接建立后，主动请求更新昨日结算价
            setTimeout(() => {
                fetch('/api/market/update_settlement_prices', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                    .then(response => response.json())
                    .then(data => {
                        console.log('昨日结算价更新请求已发送:', data);
                        dispatch(addLog(`昨日结算价更新: ${data.message || '请求已发送'}`));
                    })
                    .catch(error => {
                        console.error('请求昨日结算价更新失败:', error);
                    });
            }, 1000); // 延迟1秒发送请求
        } else if (type === 'error') {
            message.error(data.message);
            dispatch(addLog(`错误: ${data.message}`));
        } else {
            console.log('未处理的消息类型:', type, data);
        }
    }, [dispatch]);

    const connect = useCallback(() => {
        if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket already connecting, skipping...');
            return;
        }

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected, skipping...');
            return;
        }

        isConnectingRef.current = true;
        console.log('Connecting to WebSocket...');

        const wsUrl = `ws://${window.location.host}/ws`;

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('WebSocket connected successfully');
                isConnectingRef.current = false;
                reconnectAttemptsRef.current = 0;
                setIsConnected(true);
                dispatch(setConnected(true));
                dispatch(addLog('WebSocket连接已建立'));

                // 订阅所有事件
                const subscribeMessage = {
                    type: 'subscribe',
                    event_types: ['*']
                };

                console.log('Sending subscription:', subscribeMessage);
                ws.send(JSON.stringify(subscribeMessage));
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);
                    handleMessage(data);
                } catch (error) {
                    console.error('解析WebSocket消息失败:', error);
                    dispatch(addLog(`WebSocket消息解析错误: ${error}`));
                }
            };

            ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                isConnectingRef.current = false;
                setIsConnected(false);
                dispatch(setConnected(false));
                dispatch(addLog(`WebSocket连接已断开 (${event.code}: ${event.reason})`));

                // 自动重连逻辑
                if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
                    reconnectAttemptsRef.current++;

                    console.log(`Attempting reconnect ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${delay}ms`);
                    dispatch(addLog(`${delay / 1000}秒后尝试重连 (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`));

                    if (reconnectTimeoutRef.current) {
                        clearTimeout(reconnectTimeoutRef.current);
                    }
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, delay);
                } else {
                    console.log('Max reconnect attempts reached');
                    dispatch(addLog('达到最大重连次数，请手动刷新页面'));
                    message.error('WebSocket连接失败，请刷新页面重试');
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                isConnectingRef.current = false;
                dispatch(addLog('WebSocket连接错误'));
            };

        } catch (error) {
            console.error('创建WebSocket连接失败:', error);
            isConnectingRef.current = false;
            dispatch(addLog(`WebSocket创建失败: ${error}`));
        }
    }, [dispatch, handleMessage]);

    const disconnect = useCallback(() => {
        console.log('Manually disconnecting WebSocket');

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (wsRef.current) {
            wsRef.current.close(1000, 'Manual disconnect');
            wsRef.current = null;
        }

        setIsConnected(false);
        dispatch(setConnected(false));
        reconnectAttemptsRef.current = maxReconnectAttempts; // 阻止自动重连
    }, [dispatch]);

    const sendMessage = useCallback((message: any) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log('Sending WebSocket message:', message);
            wsRef.current.send(JSON.stringify(message));
            return true;
        } else {
            console.warn('WebSocket not connected, cannot send message:', message);
            return false;
        }
    }, []);

    // 初始化连接
    useEffect(() => {
        console.log('WebSocketProvider: Initializing connection');
        connect();

        // 清理函数
        return () => {
            console.log('WebSocketProvider: Cleaning up connection');
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close(1000, 'Component unmount');
            }
        };
    }, [connect]);

    const contextValue: WebSocketContextType = {
        isConnected,
        sendMessage,
        connect,
        disconnect,
    };

    return (
        <WebSocketContext.Provider value={contextValue}>
            {children}
        </WebSocketContext.Provider>
    );
}; 