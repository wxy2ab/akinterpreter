import { BarChartOutlined, DownloadOutlined, FallOutlined, LineChartOutlined, ReloadOutlined, RiseOutlined, TrophyOutlined } from '@ant-design/icons';
import { Line } from '@ant-design/plots';
import { Button, Card, Col, DatePicker, Form, Input, message, Modal, Progress, Row, Select, Space, Spin, Statistic, Table, Tabs, Tag } from 'antd';
import dayjs from 'dayjs';
import React, { useCallback, useEffect, useState } from 'react';

const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

// 类型定义
interface BasicStatistics {
    total_trades: number;
    profit_trades: number;
    loss_trades: number;
    win_rate: number;
    avg_profit: number;
    avg_loss: number;
    avg_pnl: number;
    max_profit: number;
    max_loss: number;
    max_consecutive_wins: number;
    max_consecutive_losses: number;
}

interface PnLStatistics {
    total_pnl: number;
    net_pnl: number;
    total_commission: number;
    total_volume: number;
    gross_profit: number;
    gross_loss: number;
    profit_factor: number;
    profit_loss_ratio: number;
}

interface RiskMetrics {
    max_drawdown: number;
    max_drawdown_percent: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
    var_95: number;
    var_99: number;
}

interface SymbolStatistics {
    symbol: string;
    total_trades: number;
    profit_trades: number;
    win_rate: number;
    total_pnl: number;
    net_pnl: number;
    avg_pnl: number;
    max_profit: number;
    max_loss: number;
    total_volume: number;
    total_commission: number;
}

interface DailyPnL {
    date: string;
    daily_pnl: number;
    cumulative_pnl: number;
}

interface TradingStatisticsData {
    period: string;
    start_date: string;
    end_date: string;
    basic_stats: BasicStatistics;
    pnl_stats: PnLStatistics;
    risk_metrics: RiskMetrics;
    symbol_stats: SymbolStatistics[];
    daily_pnl: DailyPnL[];
    report_content: string;
    generated_at: string;
}

interface StatisticsRequest {
    period: string;
    start_date?: string;
    end_date?: string;
    target_date?: string;
    symbols?: string[];
    use_trade_log?: boolean;
}

interface TradingStatisticsPanelProps {
    className?: string;
}

const TradingStatisticsPanel: React.FC<TradingStatisticsPanelProps> = ({ className = '' }) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [statistics, setStatistics] = useState<TradingStatisticsData | null>(null);
    const [reportModalVisible, setReportModalVisible] = useState(false);
    const [symbols, setSymbols] = useState<string[]>([]);
    const [activeTab, setActiveTab] = useState('overview');

    // 获取可用合约列表
    const fetchSymbols = useCallback(async () => {
        try {
            const response = await fetch('/api/trading-statistics/symbols');
            const data = await response.json();
            setSymbols(data.symbols || []);
        } catch (error) {
            console.error('获取合约列表失败:', error);
        }
    }, []);

    // 初始化数据
    useEffect(() => {
        fetchSymbols();
        // 默认加载今日统计
        loadQuickStats('daily');
    }, [fetchSymbols]);

    // 加载快速统计
    const loadQuickStats = async (period: string) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/trading-statistics/quick-stats?period=${period}`);
            const data = await response.json();

            // 转换为完整的统计数据格式
            const fullStats: TradingStatisticsData = {
                period: data.period,
                start_date: dayjs().format('YYYY-MM-DD'),
                end_date: dayjs().format('YYYY-MM-DD'),
                basic_stats: data.basic_stats,
                pnl_stats: data.pnl_stats,
                risk_metrics: data.risk_metrics,
                symbol_stats: [],
                daily_pnl: [],
                report_content: '',
                generated_at: data.generated_at
            };

            setStatistics(fullStats);
            form.setFieldValue('period', period);
        } catch (error) {
            console.error('加载快速统计失败:', error);
            message.error('加载统计数据失败');
        } finally {
            setLoading(false);
        }
    };

    // 生成统计
    const generateStatistics = async () => {
        setLoading(true);
        try {
            const values = await form.validateFields();

            const request: StatisticsRequest = {
                period: values.period,
                symbols: values.symbols,
                use_trade_log: values.use_trade_log || false
            };

            // 根据日期选择方式设置日期
            if (values.date_mode === 'range' && values.date_range) {
                request.start_date = values.date_range[0].format('YYYY-MM-DD');
                request.end_date = values.date_range[1].format('YYYY-MM-DD');
            } else if (values.target_date) {
                request.target_date = values.target_date.format('YYYY-MM-DD');
            }

            const response = await fetch('/api/trading-statistics/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error('统计计算失败');
            }

            const data = await response.json();
            setStatistics(data);
            message.success('统计生成完成');
        } catch (error) {
            console.error('生成统计失败:', error);
            message.error('生成统计失败');
        } finally {
            setLoading(false);
        }
    };

    // 保存报告
    const saveReport = async () => {
        if (!statistics) {
            message.warning('暂无报告可保存');
            return;
        }

        try {
            const blob = new Blob([statistics.report_content], { type: 'text/markdown' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `trading_report_${statistics.period}_${dayjs().format('YYYYMMDD_HHmmss')}.md`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            message.success('报告已保存');
        } catch (error) {
            console.error('保存报告失败:', error);
            message.error('保存报告失败');
        }
    };

    // 生成测试数据
    const generateTestData = async () => {
        try {
            const response = await fetch('/api/trading-statistics/test-data/generate', {
                method: 'POST',
            });
            const data = await response.json();

            if (data.success) {
                message.success('测试数据生成成功');
                // 重新加载统计
                loadQuickStats('daily');
            } else {
                message.error('生成测试数据失败');
            }
        } catch (error) {
            console.error('生成测试数据失败:', error);
            message.error('生成测试数据失败');
        }
    };

    // 基本统计表格列定义
    const basicStatsColumns = [
        {
            title: '指标',
            dataIndex: 'metric',
            key: 'metric',
            width: '40%',
        },
        {
            title: '数值',
            dataIndex: 'value',
            key: 'value',
            width: '30%',
            render: (value: any) => (
                <span style={{ fontWeight: 'bold' }}>{value}</span>
            ),
        },
        {
            title: '说明',
            dataIndex: 'description',
            key: 'description',
            width: '30%',
        },
    ];

    // 盈亏统计表格列定义
    const pnlStatsColumns = [
        {
            title: '指标',
            dataIndex: 'metric',
            key: 'metric',
            width: '40%',
        },
        {
            title: '数值',
            dataIndex: 'value',
            key: 'value',
            width: '30%',
            render: (value: any, record: any) => {
                const isPositive = typeof value === 'number' && value > 0;
                const isNegative = typeof value === 'number' && value < 0;
                const color = isPositive ? '#52c41a' : isNegative ? '#f5222d' : '#000';
                return (
                    <span style={{ fontWeight: 'bold', color }}>{value}</span>
                );
            },
        },
        {
            title: '说明',
            dataIndex: 'description',
            key: 'description',
            width: '30%',
        },
    ];

    // 风险指标表格列定义
    const riskMetricsColumns = [
        {
            title: '指标',
            dataIndex: 'metric',
            key: 'metric',
            width: '40%',
        },
        {
            title: '数值',
            dataIndex: 'value',
            key: 'value',
            width: '30%',
            render: (value: any) => (
                <span style={{ fontWeight: 'bold' }}>{value}</span>
            ),
        },
        {
            title: '评级',
            dataIndex: 'rating',
            key: 'rating',
            width: '30%',
            render: (rating: string) => {
                const colorMap: { [key: string]: string } = {
                    '优秀': '#52c41a',
                    '良好': '#1890ff',
                    '一般': '#faad14',
                    '较差': '#f5222d',
                    '未知': '#d9d9d9'
                };
                return (
                    <Tag color={colorMap[rating] || colorMap['未知']}>{rating}</Tag>
                );
            },
        },
    ];

    // 合约统计表格列定义
    const symbolStatsColumns = [
        {
            title: '合约',
            dataIndex: 'symbol',
            key: 'symbol',
            width: '15%',
            render: (symbol: string) => (
                <Tag color="blue">{symbol}</Tag>
            ),
        },
        {
            title: '交易次数',
            dataIndex: 'total_trades',
            key: 'total_trades',
            width: '12%',
            align: 'center' as const,
        },
        {
            title: '盈利次数',
            dataIndex: 'profit_trades',
            key: 'profit_trades',
            width: '12%',
            align: 'center' as const,
        },
        {
            title: '胜率',
            dataIndex: 'win_rate',
            key: 'win_rate',
            width: '12%',
            align: 'center' as const,
            render: (rate: number) => (
                <span style={{ color: rate >= 50 ? '#52c41a' : '#f5222d' }}>
                    {rate.toFixed(1)}%
                </span>
            ),
        },
        {
            title: '净盈亏',
            dataIndex: 'net_pnl',
            key: 'net_pnl',
            width: '15%',
            align: 'right' as const,
            render: (pnl: number) => (
                <span style={{
                    color: pnl > 0 ? '#52c41a' : pnl < 0 ? '#f5222d' : '#000',
                    fontWeight: 'bold'
                }}>
                    {pnl.toFixed(2)}
                </span>
            ),
        },
        {
            title: '平均盈亏',
            dataIndex: 'avg_pnl',
            key: 'avg_pnl',
            width: '15%',
            align: 'right' as const,
            render: (pnl: number) => (
                <span style={{ color: pnl > 0 ? '#52c41a' : pnl < 0 ? '#f5222d' : '#000' }}>
                    {pnl.toFixed(2)}
                </span>
            ),
        },
        {
            title: '成交量',
            dataIndex: 'total_volume',
            key: 'total_volume',
            width: '12%',
            align: 'center' as const,
        },
        {
            title: '手续费',
            dataIndex: 'total_commission',
            key: 'total_commission',
            width: '12%',
            align: 'right' as const,
            render: (commission: number) => commission.toFixed(2),
        },
    ];

    // 准备基本统计数据
    const prepareBasicStatsData = (stats: BasicStatistics) => [
        { key: '1', metric: '总交易次数', value: stats.total_trades, description: '所有交易的总数量' },
        { key: '2', metric: '盈利交易次数', value: stats.profit_trades, description: '盈利交易的数量' },
        { key: '3', metric: '亏损交易次数', value: stats.loss_trades, description: '亏损交易的数量' },
        { key: '4', metric: '胜率', value: `${stats.win_rate.toFixed(1)}%`, description: '盈利交易占总交易的比例' },
        { key: '5', metric: '平均盈利', value: stats.avg_profit.toFixed(2), description: '每笔盈利交易的平均盈利' },
        { key: '6', metric: '平均亏损', value: stats.avg_loss.toFixed(2), description: '每笔亏损交易的平均亏损' },
        { key: '7', metric: '平均盈亏', value: stats.avg_pnl.toFixed(2), description: '每笔交易的平均盈亏' },
        { key: '8', metric: '最大盈利', value: stats.max_profit.toFixed(2), description: '单笔交易的最大盈利' },
        { key: '9', metric: '最大亏损', value: stats.max_loss.toFixed(2), description: '单笔交易的最大亏损' },
        { key: '10', metric: '最大连续盈利', value: stats.max_consecutive_wins, description: '连续盈利的最大次数' },
        { key: '11', metric: '最大连续亏损', value: stats.max_consecutive_losses, description: '连续亏损的最大次数' },
    ];

    // 准备盈亏统计数据
    const preparePnLStatsData = (stats: PnLStatistics) => [
        { key: '1', metric: '总盈亏', value: stats.total_pnl.toFixed(2), description: '所有交易的盈亏总和' },
        { key: '2', metric: '净盈亏', value: stats.net_pnl.toFixed(2), description: '扣除手续费后的盈亏' },
        { key: '3', metric: '总手续费', value: stats.total_commission.toFixed(2), description: '所有交易的手续费总和' },
        { key: '4', metric: '总成交量', value: stats.total_volume.toString(), description: '所有交易的成交量总和' },
        { key: '5', metric: '总盈利', value: stats.gross_profit.toFixed(2), description: '所有盈利交易的盈利总和' },
        { key: '6', metric: '总亏损', value: stats.gross_loss.toFixed(2), description: '所有亏损交易的亏损总和' },
        { key: '7', metric: '盈利因子', value: stats.profit_factor.toFixed(2), description: '总盈利与总亏损的比值' },
        { key: '8', metric: '盈亏比', value: stats.profit_loss_ratio.toFixed(2), description: '平均盈利与平均亏损的比值' },
    ];

    // 准备风险指标数据
    const prepareRiskMetricsData = (metrics: RiskMetrics) => {
        const getRating = (value: number, type: string) => {
            switch (type) {
                case 'sharpe':
                    if (value >= 2) return '优秀';
                    if (value >= 1) return '良好';
                    if (value >= 0.5) return '一般';
                    return '较差';
                case 'drawdown':
                    if (value <= 5) return '优秀';
                    if (value <= 10) return '良好';
                    if (value <= 20) return '一般';
                    return '较差';
                default:
                    return '未知';
            }
        };

        return [
            {
                key: '1',
                metric: '最大回撤',
                value: metrics.max_drawdown.toFixed(2),
                rating: getRating(metrics.max_drawdown_percent, 'drawdown'),
                description: '最大回撤金额'
            },
            {
                key: '2',
                metric: '最大回撤百分比',
                value: `${metrics.max_drawdown_percent.toFixed(2)}%`,
                rating: getRating(metrics.max_drawdown_percent, 'drawdown'),
                description: '最大回撤百分比'
            },
            {
                key: '3',
                metric: '夏普比率',
                value: metrics.sharpe_ratio.toFixed(2),
                rating: getRating(metrics.sharpe_ratio, 'sharpe'),
                description: '风险调整后收益'
            },
            {
                key: '4',
                metric: '索提诺比率',
                value: metrics.sortino_ratio.toFixed(2),
                rating: getRating(metrics.sortino_ratio, 'sharpe'),
                description: '下行风险调整后收益'
            },
            {
                key: '5',
                metric: '卡玛比率',
                value: metrics.calmar_ratio.toFixed(2),
                rating: '未知',
                description: '年化收益率与最大回撤的比值'
            },
            {
                key: '6',
                metric: '95% VaR',
                value: metrics.var_95.toFixed(2),
                rating: '未知',
                description: '95%置信度下的风险价值'
            },
            {
                key: '7',
                metric: '99% VaR',
                value: metrics.var_99.toFixed(2),
                rating: '未知',
                description: '99%置信度下的风险价值'
            },
        ];
    };

    // 准备盈亏曲线数据
    const preparePnLChartData = (dailyPnL: DailyPnL[]) => {
        return dailyPnL.map(item => ({
            date: item.date,
            value: item.cumulative_pnl,
            category: '累计盈亏'
        }));
    };

    return (
        <div className={`trading-statistics-panel ${className}`}>
            <Card title="交易统计分析" className="h-full">
                <div className="flex flex-col h-full">
                    {/* 控制面板 */}
                    <Card size="small" className="mb-4">
                        <Form
                            form={form}
                            layout="inline"
                            initialValues={{
                                period: 'daily',
                                date_mode: 'target',
                                target_date: dayjs(),
                                use_trade_log: false,
                            }}
                        >
                            <Form.Item name="period" label="统计周期">
                                <Select style={{ width: 120 }}>
                                    <Option value="daily">日度</Option>
                                    <Option value="weekly">周度</Option>
                                    <Option value="monthly">月度</Option>
                                    <Option value="quarterly">季度</Option>
                                    <Option value="yearly">年度</Option>
                                </Select>
                            </Form.Item>

                            <Form.Item name="date_mode" label="日期模式">
                                <Select style={{ width: 120 }}>
                                    <Option value="target">目标日期</Option>
                                    <Option value="range">日期范围</Option>
                                </Select>
                            </Form.Item>

                            <Form.Item
                                noStyle
                                shouldUpdate={(prevValues, currentValues) =>
                                    prevValues.date_mode !== currentValues.date_mode
                                }
                            >
                                {({ getFieldValue }) => {
                                    return getFieldValue('date_mode') === 'range' ? (
                                        <Form.Item name="date_range" label="日期范围">
                                            <RangePicker />
                                        </Form.Item>
                                    ) : (
                                        <Form.Item name="target_date" label="目标日期">
                                            <DatePicker />
                                        </Form.Item>
                                    );
                                }}
                            </Form.Item>

                            <Form.Item name="symbols" label="合约过滤">
                                <Select
                                    mode="multiple"
                                    style={{ width: 200 }}
                                    placeholder="选择合约（不选择则统计所有）"
                                    allowClear
                                >
                                    {symbols.map(symbol => (
                                        <Option key={symbol} value={symbol}>{symbol}</Option>
                                    ))}
                                </Select>
                            </Form.Item>

                            <Form.Item>
                                <Space>
                                    <Button
                                        type="primary"
                                        icon={<BarChartOutlined />}
                                        onClick={generateStatistics}
                                        loading={loading}
                                    >
                                        生成统计
                                    </Button>
                                    <Button
                                        icon={<ReloadOutlined />}
                                        onClick={() => loadQuickStats('daily')}
                                    >
                                        今日快速统计
                                    </Button>
                                    <Button
                                        icon={<DownloadOutlined />}
                                        onClick={saveReport}
                                        disabled={!statistics}
                                    >
                                        保存报告
                                    </Button>
                                    <Button
                                        onClick={generateTestData}
                                        type="dashed"
                                    >
                                        生成测试数据
                                    </Button>
                                </Space>
                            </Form.Item>
                        </Form>
                    </Card>

                    {/* 主要内容区域 */}
                    <div className="flex-1">
                        <Spin spinning={loading}>
                            {statistics ? (
                                <Tabs
                                    activeKey={activeTab}
                                    onChange={setActiveTab}
                                    className="h-full"
                                >
                                    {/* 概览统计 */}
                                    <TabPane tab={<span><TrophyOutlined />概览</span>} key="overview">
                                        <Row gutter={[16, 16]}>
                                            <Col span={6}>
                                                <Card size="small">
                                                    <Statistic
                                                        title="总交易次数"
                                                        value={statistics.basic_stats.total_trades}
                                                        prefix={<BarChartOutlined />}
                                                    />
                                                </Card>
                                            </Col>
                                            <Col span={6}>
                                                <Card size="small">
                                                    <Statistic
                                                        title="胜率"
                                                        value={statistics.basic_stats.win_rate}
                                                        precision={1}
                                                        suffix="%"
                                                        valueStyle={{ color: statistics.basic_stats.win_rate >= 50 ? '#3f8600' : '#cf1322' }}
                                                        prefix={<TrophyOutlined />}
                                                    />
                                                </Card>
                                            </Col>
                                            <Col span={6}>
                                                <Card size="small">
                                                    <Statistic
                                                        title="净盈亏"
                                                        value={statistics.pnl_stats.net_pnl}
                                                        precision={2}
                                                        valueStyle={{ color: statistics.pnl_stats.net_pnl >= 0 ? '#3f8600' : '#cf1322' }}
                                                        prefix={statistics.pnl_stats.net_pnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
                                                    />
                                                </Card>
                                            </Col>
                                            <Col span={6}>
                                                <Card size="small">
                                                    <Statistic
                                                        title="盈利因子"
                                                        value={statistics.pnl_stats.profit_factor}
                                                        precision={2}
                                                        valueStyle={{ color: statistics.pnl_stats.profit_factor >= 1 ? '#3f8600' : '#cf1322' }}
                                                    />
                                                </Card>
                                            </Col>
                                        </Row>

                                        <Row gutter={[16, 16]} className="mt-4">
                                            <Col span={12}>
                                                <Card size="small" title="胜率分布">
                                                    <div className="flex items-center space-x-4">
                                                        <div className="flex-1">
                                                            <div className="text-sm text-gray-500 mb-1">盈利交易</div>
                                                            <Progress
                                                                percent={statistics.basic_stats.win_rate}
                                                                strokeColor="#52c41a"
                                                                showInfo={false}
                                                            />
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-lg font-bold text-green-600">
                                                                {statistics.basic_stats.profit_trades}
                                                            </div>
                                                            <div className="text-sm text-gray-500">盈利次数</div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center space-x-4 mt-2">
                                                        <div className="flex-1">
                                                            <div className="text-sm text-gray-500 mb-1">亏损交易</div>
                                                            <Progress
                                                                percent={100 - statistics.basic_stats.win_rate}
                                                                strokeColor="#f5222d"
                                                                showInfo={false}
                                                            />
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-lg font-bold text-red-600">
                                                                {statistics.basic_stats.loss_trades}
                                                            </div>
                                                            <div className="text-sm text-gray-500">亏损次数</div>
                                                        </div>
                                                    </div>
                                                </Card>
                                            </Col>
                                            <Col span={12}>
                                                <Card size="small" title="盈亏对比">
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="text-center">
                                                            <div className="text-2xl font-bold text-green-600">
                                                                {statistics.pnl_stats.gross_profit.toFixed(2)}
                                                            </div>
                                                            <div className="text-sm text-gray-500">总盈利</div>
                                                        </div>
                                                        <div className="text-center">
                                                            <div className="text-2xl font-bold text-red-600">
                                                                {statistics.pnl_stats.gross_loss.toFixed(2)}
                                                            </div>
                                                            <div className="text-sm text-gray-500">总亏损</div>
                                                        </div>
                                                    </div>
                                                </Card>
                                            </Col>
                                        </Row>
                                    </TabPane>

                                    {/* 基本统计 */}
                                    <TabPane tab={<span><BarChartOutlined />基本统计</span>} key="basic">
                                        <Table
                                            columns={basicStatsColumns}
                                            dataSource={prepareBasicStatsData(statistics.basic_stats)}
                                            pagination={false}
                                            size="small"
                                            className="statistics-table"
                                        />
                                    </TabPane>

                                    {/* 盈亏统计 */}
                                    <TabPane tab={<span><RiseOutlined />盈亏统计</span>} key="pnl">
                                        <Table
                                            columns={pnlStatsColumns}
                                            dataSource={preparePnLStatsData(statistics.pnl_stats)}
                                            pagination={false}
                                            size="small"
                                            className="statistics-table"
                                        />
                                    </TabPane>

                                    {/* 风险指标 */}
                                    <TabPane tab={<span><FallOutlined />风险指标</span>} key="risk">
                                        <Table
                                            columns={riskMetricsColumns}
                                            dataSource={prepareRiskMetricsData(statistics.risk_metrics)}
                                            pagination={false}
                                            size="small"
                                            className="statistics-table"
                                        />
                                    </TabPane>

                                    {/* 分合约统计 */}
                                    <TabPane tab={<span><BarChartOutlined />分合约统计</span>} key="symbols">
                                        <Table
                                            columns={symbolStatsColumns}
                                            dataSource={statistics.symbol_stats}
                                            pagination={{ pageSize: 10 }}
                                            size="small"
                                            className="statistics-table"
                                            scroll={{ y: 400 }}
                                        />
                                    </TabPane>

                                    {/* 盈亏曲线 */}
                                    <TabPane tab={<span><LineChartOutlined />盈亏曲线</span>} key="chart">
                                        {statistics.daily_pnl.length > 0 ? (
                                            <Line
                                                data={preparePnLChartData(statistics.daily_pnl)}
                                                xField="date"
                                                yField="value"
                                                seriesField="category"
                                                height={400}
                                                smooth={true}
                                                color={['#1890ff']}
                                                point={{
                                                    size: 3,
                                                    shape: 'circle',
                                                }}
                                                tooltip={{
                                                    formatter: (datum: any) => {
                                                        return {
                                                            name: '累计盈亏',
                                                            value: `${datum.value.toFixed(2)}`,
                                                        };
                                                    },
                                                }}
                                            />
                                        ) : (
                                            <div className="text-center py-20 text-gray-500">
                                                暂无盈亏曲线数据
                                            </div>
                                        )}
                                    </TabPane>

                                    {/* 统计报告 */}
                                    <TabPane tab={<span><DownloadOutlined />统计报告</span>} key="report">
                                        <div className="h-96">
                                            <TextArea
                                                value={statistics.report_content}
                                                readOnly
                                                className="h-full"
                                                placeholder="统计报告内容将显示在此处..."
                                            />
                                        </div>
                                    </TabPane>
                                </Tabs>
                            ) : (
                                <div className="text-center py-20 text-gray-500">
                                    请点击"生成统计"或"今日快速统计"加载数据
                                </div>
                            )}
                        </Spin>
                    </div>
                </div>
            </Card>

            {/* 报告预览模态框 */}
            <Modal
                title="统计报告预览"
                open={reportModalVisible}
                onCancel={() => setReportModalVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setReportModalVisible(false)}>
                        关闭
                    </Button>,
                    <Button key="save" type="primary" onClick={saveReport}>
                        保存
                    </Button>,
                ]}
                width={800}
            >
                <div className="max-h-96 overflow-auto">
                    <pre className="whitespace-pre-wrap text-sm">
                        {statistics?.report_content}
                    </pre>
                </div>
            </Modal>
        </div>
    );
};

export default TradingStatisticsPanel; 