import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { Provider } from 'react-redux';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';

import './App.css';
import LoginPage from './components/Auth/LoginPage';
import MainLayout from './components/Layout/MainLayout';
import { WebSocketProvider } from './context/WebSocketContext';
import { store } from './store/store';

const App: React.FC = () => {
    const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        // 检查CTP服务状态，而不是localStorage
        checkCTPStatus();
    }, []);

    const checkCTPStatus = async () => {
        try {
            const response = await axios.get('/api/system/status');
            const { ctp_connected, ctp_kernel_running } = response.data;

            // 🔧 新逻辑：如果CTP内核已经运行，直接进入dashboard
            if (ctp_kernel_running) {
                localStorage.setItem('isLoggedIn', 'true');
                localStorage.setItem('loginMethod', 'auto_detected');
                setIsLoggedIn(true);
                console.log('检测到CTP服务已启动，自动登录成功');
            } else {
                // CTP未启动，显示登录页面让用户手动启动
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('currentUser');
                localStorage.removeItem('loginMethod');
                setIsLoggedIn(false);
                console.log('CTP服务未启动，需要用户登录启动');
            }
        } catch (error) {
            console.error('检查CTP状态失败:', error);
            // 网络错误时也清除登录状态
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('currentUser');
            localStorage.removeItem('loginMethod');
            setIsLoggedIn(false);
        } finally {
            setLoading(false);
        }
    };

    // 登录成功回调
    const handleLoginSuccess = () => {
        setIsLoggedIn(true);
    };

    // 退出登录回调
    const handleLogout = async () => {
        try {
            // 停止CTP服务
            await axios.post('/api/system/stop-ctp');
        } catch (error) {
            console.error('停止CTP服务失败:', error);
        }

        // 清除登录状态
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('currentUser');
        setIsLoggedIn(false);
    };

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh'
            }}>
                加载中...
            </div>
        );
    }

    return (
        <Provider store={store}>
            <ConfigProvider locale={zhCN}>
                <Router>
                    <Routes>
                        <Route
                            path="/login"
                            element={
                                isLoggedIn ?
                                    <Navigate to="/dashboard" replace /> :
                                    <LoginPage onLoginSuccess={handleLoginSuccess} />
                            }
                        />
                        <Route
                            path="/*"
                            element={
                                isLoggedIn ? (
                                    <WebSocketProvider>
                                        <MainLayout onLogout={handleLogout} />
                                    </WebSocketProvider>
                                ) : (
                                    <Navigate to="/login" replace />
                                )
                            }
                        />
                    </Routes>
                </Router>
            </ConfigProvider>
        </Provider>
    );
};

export default App; 