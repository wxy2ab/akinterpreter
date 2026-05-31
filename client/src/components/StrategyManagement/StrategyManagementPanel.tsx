import {
    ControlOutlined,
    ExclamationCircleOutlined,
    EyeOutlined,
    ReloadOutlined,
    SafetyCertificateOutlined,
    SettingOutlined
} from '@ant-design/icons';
import { Button, message, Modal, Spin, Tabs } from 'antd';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import RiskManagementPanel from './RiskManagementPanel';
import StrategyConfigEditor from './StrategyConfigEditor';
import './StrategyManagementPanel.css';
import StrategyStatusTable from './StrategyStatusTable';
import SymbolMonitoringTable from './SymbolMonitoringTable';

const { TabPane } = Tabs;
const { confirm } = Modal;

// 数据接口定义
interface StrategyInfo {
    name: string;
    enabled: boolean;
    symbols: string[];
    alpha_threshold: number;
    position_multiplier: number | { [key: string]: number } | null;
    greed_position: boolean;
    freq: string;
    init_bars: number;
    risk_status: string;
}

interface MonitoredSymbol {
    symbol: string;
    product: string;
    strategy_name: string;
    added_time: string;
}

interface RiskConfig {
    enabled: boolean;
    max_order_size: number;
    max_position_size: number;
    stop_loss_pct: number;
    daily_loss_limit: number;
}

interface RiskStatus {
    enabled: boolean;
    daily_pnl: number;
    current_position: number;
    risk_level: string;
    last_updated: string;
}

interface StatisticsData {
    total_strategies: number;
    enabled_strategies: number;
    disabled_strategies: number;
    total_symbols: number;
    risk_controlled_strategies: number;
    strategies_by_freq: { [key: string]: number };
    symbols_by_product: { [key: string]: number };
    last_updated: string;
}

const StrategyManagementPanel: React.FC = () => {
    // 状态管理
    const [activeTab, setActiveTab] = useState<string>('strategies');
    const [loading, setLoading] = useState<boolean>(false);
    const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
    const [symbols, setSymbols] = useState<MonitoredSymbol[]>([]);
    const [riskConfig, setRiskConfig] = useState<RiskConfig>({
        enabled: true,
        max_order_size: 9999,
        max_position_size: 50,
        stop_loss_pct: 2.0,
        daily_loss_limit: 50000
    });
    const [riskStatus, setRiskStatus] = useState<RiskStatus>({
        enabled: true,
        daily_pnl: 0,
        current_position: 0,
        risk_level: '正常',
        last_updated: new Date().toISOString()
    });
    const [statistics, setStatistics] = useState<StatisticsData>({
        total_strategies: 0,
        enabled_strategies: 0,
        disabled_strategies: 0,
        total_symbols: 0,
        risk_controlled_strategies: 0,
        strategies_by_freq: {},
        symbols_by_product: {},
        last_updated: new Date().toISOString()
    });

    // WebSocket连接
    const { isConnected, sendMessage, subscribe, unsubscribe } = useWebSocket();

    // 处理WebSocket消息
    const handleWebSocketMessage = useCallback((data: any) => {
        const { type, data: messageData } = data;

        switch (type) {
            case 'strategy_management_strategy_enabled_changed':
                handleStrategyEnabledChanged(messageData);
                break;
            case 'strategy_management_strategy_config_changed':
                handleStrategyConfigChanged(messageData);
                break;
            case 'strategy_management_symbol_added':
                handleSymbolAdded(messageData);
                break;
            case 'strategy_management_symbol_removed':
                handleSymbolRemoved(messageData);
                break;
            case 'strategy_management_risk_config_changed':
                handleRiskConfigChanged(messageData);
                break;
            case 'strategy_management_risk_status_changed':
                handleRiskStatusChanged(messageData);
                break;
            case 'strategy_management_emergency_stop_triggered':
                handleEmergencyStopTriggered(messageData);
                break;
            case 'strategy_management_strategy_activity_update':
                handleStrategyActivityUpdate(messageData);
                break;
            default:
                break;
        }
    }, []);

    // WebSocket事件处理函数
    const handleStrategyEnabledChanged = useCallback((data: any) => {
        const { strategy_name, enabled } = data;
        setStrategies(prev => prev.map(strategy =>
            strategy.name === strategy_name
                ? { ...strategy, enabled }
                : strategy
        ));
        message.info(`策略 ${strategy_name} 已${enabled ? '启用' : '禁用'}`);
    }, []);

    const handleStrategyConfigChanged = useCallback((data: any) => {
        const { strategy_name, config } = data;
        setStrategies(prev => prev.map(strategy =>
            strategy.name === strategy_name
                ? { ...strategy, ...config }
                : strategy
        ));
        message.success(`策略 ${strategy_name} 配置已更新`);
    }, []);

    const handleSymbolAdded = useCallback((data: any) => {
        const { symbol, strategy_name } = data;
        loadSymbols(); // 重新加载合约列表
        message.success(`已添加监控合约: ${symbol}`);
    }, []);

    const handleSymbolRemoved = useCallback((data: any) => {
        const { symbol } = data;
        setSymbols(prev => prev.filter(s => s.symbol !== symbol));
        message.success(`已删除监控合约: ${symbol}`);
    }, []);

    const handleRiskConfigChanged = useCallback((data: any) => {
        const { config } = data;
        setRiskConfig(config);
        message.success('风控配置已更新');
    }, []);

    const handleRiskStatusChanged = useCallback((data: any) => {
        const { status } = data;
        setRiskStatus(status);
    }, []);

    const handleEmergencyStopTriggered = useCallback((data: any) => {
        const { reason } = data;
        Modal.error({
            title: '紧急停止已触发',
            content: `原因: ${reason}`,
            icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
        });
        // 重新加载策略状态
        loadStrategies();
    }, []);

    const handleStrategyActivityUpdate = useCallback((data: any) => {
        // 更新策略活跃状态，但不显示消息避免干扰
        const { strategy_name, last_signal_time } = data;
        setStrategies(prev => prev.map(strategy =>
            strategy.name === strategy_name
                ? { ...strategy, last_active: last_signal_time }
                : strategy
        ));
    }, []);

    // API调用函数
    const loadStrategies = useCallback(async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/strategy-management/strategies');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                setStrategies(result.data || []);
            } else {
                throw new Error(result.message || '获取策略列表失败');
            }
        } catch (error) {
            console.error('加载策略列表失败:', error);
            message.error(`加载策略列表失败: ${error instanceof Error ? error.message : String(error)}`);
            setStrategies([]); // 清空数据，显示真实错误状态
        } finally {
            setLoading(false);
        }
    }, []);

    const loadSymbols = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-management/symbols');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                setSymbols(result.data || []);
            } else {
                throw new Error(result.message || '获取监控合约失败');
            }
        } catch (error) {
            console.error('加载监控合约失败:', error);
            message.error(`加载监控合约列表失败: ${error instanceof Error ? error.message : String(error)}`);
            setSymbols([]); // 清空数据，显示真实错误状态
        }
    }, []);

    const loadRiskConfig = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-management/risk/config');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                setRiskConfig(result.data);
            } else {
                throw new Error(result.message || '获取风控配置失败');
            }
        } catch (error) {
            console.error('加载风控配置失败:', error);
            message.error(`加载风控配置失败: ${error instanceof Error ? error.message : String(error)}`);
            setRiskConfig({
                enabled: true,
                max_order_size: 9999,
                max_position_size: 50,
                stop_loss_pct: 2.0,
                daily_loss_limit: 50000
            }); // 使用默认值而不是null
        }
    }, []);

    const loadRiskStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-management/risk/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                setRiskStatus(result.data);
            } else {
                throw new Error(result.message || '获取风控状态失败');
            }
        } catch (error) {
            console.error('加载风控状态失败:', error);
            message.error(`加载风控状态失败: ${error instanceof Error ? error.message : String(error)}`);
            setRiskStatus({
                enabled: true,
                daily_pnl: 0,
                current_position: 0,
                risk_level: '正常',
                last_updated: new Date().toISOString()
            }); // 使用默认值而不是null
        }
    }, []);

    const loadStatistics = useCallback(async () => {
        try {
            const response = await fetch('/api/strategy-management/statistics');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                setStatistics(result.data);
            } else {
                throw new Error(result.message || '获取统计信息失败');
            }
        } catch (error) {
            console.error('加载统计信息失败:', error);
            message.error(`加载统计信息失败: ${error instanceof Error ? error.message : String(error)}`);
            setStatistics({
                total_strategies: 0,
                enabled_strategies: 0,
                disabled_strategies: 0,
                total_symbols: 0,
                risk_controlled_strategies: 0,
                strategies_by_freq: {},
                symbols_by_product: {},
                last_updated: new Date().toISOString()
            }); // 使用默认值而不是null
        }
    }, []);

    // 批量操作函数
    const enableAllStrategies = useCallback(async () => {
        try {
            setLoading(true);
            const strategyNames = strategies.map(s => s.name);
            const response = await fetch('/api/strategy-management/strategies/batch-enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strategy_names: strategyNames, enabled: true })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            if (result.success) {
                message.success(result.message);
                loadStrategies();
            } else {
                throw new Error(result.message || '批量启用策略失败');
            }
        } catch (error) {
            console.error('批量启用策略失败:', error);
            message.error(`批量启用策略失败: ${error instanceof Error ? error.message : String(error)}`);
        } finally {
            setLoading(false);
        }
    }, [strategies, loadStrategies]);

    const disableAllStrategies = useCallback(async () => {
        confirm({
            title: '确认禁用所有策略？',
            content: '这将禁用所有策略，停止自动交易',
            icon: <ExclamationCircleOutlined />,
            onOk: async () => {
                try {
                    setLoading(true);
                    const strategyNames = strategies.map(s => s.name);
                    const response = await fetch('/api/strategy-management/strategies/batch-enable', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ strategy_names: strategyNames, enabled: false })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();
                    if (result.success) {
                        message.success(result.message);
                        loadStrategies();
                    } else {
                        throw new Error(result.message || '批量禁用策略失败');
                    }
                } catch (error) {
                    console.error('批量禁用策略失败:', error);
                    message.error(`批量禁用策略失败: ${error instanceof Error ? error.message : String(error)}`);
                } finally {
                    setLoading(false);
                }
            }
        });
    }, [strategies, loadStrategies]);

    // 刷新所有数据
    const refreshAllData = useCallback(async () => {
        setLoading(true);
        try {
            await Promise.all([
                loadStrategies(),
                loadSymbols(),
                loadRiskConfig(),
                loadRiskStatus(),
                loadStatistics()
            ]);
            message.success('数据已刷新');
        } catch (error) {
            message.error('刷新数据失败');
        } finally {
            setLoading(false);
        }
    }, [loadStrategies, loadSymbols, loadRiskConfig, loadRiskStatus, loadStatistics]);

    // 组件挂载时加载数据
    useEffect(() => {
        loadStrategies();
        loadSymbols();
        loadRiskConfig();
        loadRiskStatus();
        loadStatistics();
    }, []);

    // 定期刷新统计信息和风控状态
    useEffect(() => {
        const interval = setInterval(() => {
            loadStatistics();
            loadRiskStatus();
        }, 30000); // 每30秒刷新一次

        return () => clearInterval(interval);
    }, [loadStatistics, loadRiskStatus]);

    // 设置WebSocket事件监听
    useEffect(() => {
        const handleMessage = (data: any) => {
            if (data.type?.startsWith('strategy_management_')) {
                handleWebSocketMessage(data);
            }
        };

        subscribe(['strategy_management_*'], handleMessage);

        return () => {
            unsubscribe(['strategy_management_*']);
        };
    }, [subscribe, unsubscribe, handleWebSocketMessage]);

    // 计算统计概览
    const overviewStats = useMemo(() => {
        return {
            totalStrategies: strategies.length,
            enabledStrategies: strategies.filter(s => s.enabled).length,
            totalSymbols: symbols.length,
            riskControlledStrategies: strategies.filter(s => s.risk_status !== '正常').length,
            activeStrategies: strategies.filter(s => s.enabled && s.risk_status === '正常').length
        };
    }, [strategies, symbols]);

    return (
        <div className="strategy-management-panel">
            {/* 头部控制栏 */}
            <div className="strategy-management-header">
                <div className="header-title">
                    <ControlOutlined className="title-icon" />
                    <span>策略管理中心</span>
                    <div className="connection-status">
                        <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                            {isConnected ? '已连接' : '未连接'}
                        </span>
                    </div>
                </div>

                <div className="header-actions">
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={refreshAllData}
                        loading={loading}
                    >
                        刷新数据
                    </Button>
                    <Button
                        type="primary"
                        onClick={enableAllStrategies}
                        loading={loading}
                        disabled={!strategies.length}
                    >
                        启用全部
                    </Button>
                    <Button
                        danger
                        onClick={disableAllStrategies}
                        loading={loading}
                        disabled={!strategies.length}
                    >
                        禁用全部
                    </Button>
                </div>
            </div>

            {/* 统计概览 */}
            <div className="overview-stats">
                <div className="stat-item">
                    <div className="stat-number">{overviewStats.totalStrategies}</div>
                    <div className="stat-label">总策略数</div>
                </div>
                <div className="stat-item">
                    <div className="stat-number active">{overviewStats.activeStrategies}</div>
                    <div className="stat-label">活跃策略</div>
                </div>
                <div className="stat-item">
                    <div className="stat-number">{overviewStats.totalSymbols}</div>
                    <div className="stat-label">监控合约</div>
                </div>
                <div className="stat-item">
                    <div className="stat-number risk">{overviewStats.riskControlledStrategies}</div>
                    <div className="stat-label">风控策略</div>
                </div>
                <div className="stat-item">
                    <div className={`stat-number ${riskStatus.daily_pnl >= 0 ? 'profit' : 'loss'}`}>
                        ¥{riskStatus.daily_pnl.toFixed(2)}
                    </div>
                    <div className="stat-label">当日盈亏</div>
                </div>
            </div>

            {/* 主要内容选项卡 */}
            <div className="strategy-management-content">
                <Spin spinning={loading}>
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        type="card"
                        className="management-tabs"
                    >
                        <TabPane
                            tab={
                                <span>
                                    <ControlOutlined />
                                    策略管理
                                </span>
                            }
                            key="strategies"
                        >
                            <StrategyStatusTable
                                strategies={strategies}
                                onStrategyEnabledChange={loadStrategies}
                                onStrategyConfigChange={loadStrategies}
                                loading={loading}
                            />
                        </TabPane>

                        <TabPane
                            tab={
                                <span>
                                    <EyeOutlined />
                                    合约监控
                                </span>
                            }
                            key="symbols"
                        >
                            <SymbolMonitoringTable
                                symbols={symbols}
                                strategies={strategies}
                                onSymbolAdded={loadSymbols}
                                onSymbolRemoved={loadSymbols}
                                loading={loading}
                            />
                        </TabPane>

                        <TabPane
                            tab={
                                <span>
                                    <SettingOutlined />
                                    策略配置
                                </span>
                            }
                            key="config"
                        >
                            <StrategyConfigEditor
                                strategies={strategies}
                                onConfigSaved={loadStrategies}
                                loading={loading}
                            />
                        </TabPane>

                        <TabPane
                            tab={
                                <span>
                                    <SafetyCertificateOutlined />
                                    风控管理
                                </span>
                            }
                            key="risk"
                        >
                            <RiskManagementPanel
                                config={riskConfig}
                                status={riskStatus}
                                onConfigChange={loadRiskConfig}
                                onStatusChange={loadRiskStatus}
                                loading={loading}
                            />
                        </TabPane>
                    </Tabs>
                </Spin>
            </div>
        </div>
    );
};

export default StrategyManagementPanel; 