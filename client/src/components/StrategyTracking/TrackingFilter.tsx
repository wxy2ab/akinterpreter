import {
    ClearOutlined,
    ClockCircleOutlined,
    FilterOutlined
} from '@ant-design/icons';
import {
    Button,
    Card,
    Col,
    DatePicker,
    Row,
    Select,
    Space,
    Tag,
    Typography
} from 'antd';
import React, { useMemo } from 'react';
import { FilterParams, StrategySignal, TradeExecution } from './StrategyTrackingPanel';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text } = Typography;

interface TrackingFilterProps {
    filterParams: FilterParams;
    onFilterChange: (params: FilterParams) => void;
    signals: StrategySignal[];
    trades: TradeExecution[];
}

export const TrackingFilter: React.FC<TrackingFilterProps> = ({
    filterParams,
    onFilterChange,
    signals,
    trades
}) => {

    // 从数据中提取可用选项
    const filterOptions = useMemo(() => {
        const strategies = Array.from(new Set([
            ...signals.map(s => s.strategy_name),
            ...trades.map(t => t.strategy_name)
        ])).sort();

        const signalTypes = Array.from(new Set(signals.map(s => s.signal_type))).sort();

        const symbols = Array.from(new Set([
            ...signals.map(s => s.symbol),
            ...trades.map(t => t.symbol)
        ])).sort();

        const executionStatuses = Array.from(new Set(trades.map(t => t.status))).sort();

        return {
            strategies,
            signalTypes,
            symbols,
            executionStatuses
        };
    }, [signals, trades]);

    // 处理过滤参数变更
    const handleFilterChange = (key: keyof FilterParams, value: any) => {
        const newParams = { ...filterParams, [key]: value };
        onFilterChange(newParams);
    };

    // 重置过滤器
    const resetFilters = () => {
        onFilterChange({
            time_range_hours: 24,
            max_items: 200
        });
    };

    // 快捷时间范围按钮
    const timeRangeButtons = [
        { label: '1小时', value: 1 },
        { label: '6小时', value: 6 },
        { label: '24小时', value: 24 },
        { label: '3天', value: 72 },
        { label: '7天', value: 168 },
        { label: '全部', value: undefined }
    ];

    return (
        <Card
            size="small"
            style={{ marginBottom: 16 }}
            title={
                <Space>
                    <FilterOutlined />
                    过滤器
                </Space>
            }
            extra={
                <Button
                    size="small"
                    icon={<ClearOutlined />}
                    onClick={resetFilters}
                >
                    重置
                </Button>
            }
        >
            <Row gutter={[16, 16]}>
                {/* 时间范围 */}
                <Col span={24}>
                    <div style={{ marginBottom: 8 }}>
                        <Text strong>
                            <ClockCircleOutlined style={{ marginRight: 4 }} />
                            时间范围
                        </Text>
                    </div>
                    <Space wrap>
                        {timeRangeButtons.map(btn => (
                            <Button
                                key={btn.label}
                                size="small"
                                type={filterParams.time_range_hours === btn.value ? 'primary' : 'default'}
                                onClick={() => handleFilterChange('time_range_hours', btn.value)}
                            >
                                {btn.label}
                            </Button>
                        ))}
                    </Space>
                </Col>

                {/* 策略名称过滤 */}
                <Col xs={24} sm={12} md={8} lg={6}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        策略名称
                    </Text>
                    <Select
                        mode="multiple"
                        placeholder="选择策略"
                        style={{ width: '100%' }}
                        value={filterParams.strategy_names || []}
                        onChange={(value) => handleFilterChange('strategy_names', value)}
                        maxTagCount={2}
                        allowClear
                    >
                        {filterOptions.strategies.map(strategy => (
                            <Option key={strategy} value={strategy}>
                                {strategy}
                            </Option>
                        ))}
                    </Select>
                </Col>

                {/* 信号类型过滤 */}
                <Col xs={24} sm={12} md={8} lg={6}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        信号类型
                    </Text>
                    <Select
                        mode="multiple"
                        placeholder="选择信号类型"
                        style={{ width: '100%' }}
                        value={filterParams.signal_types || []}
                        onChange={(value) => handleFilterChange('signal_types', value)}
                        maxTagCount={2}
                        allowClear
                    >
                        {filterOptions.signalTypes.map(type => (
                            <Option key={type} value={type}>
                                <Tag
                                    color={
                                        ['buy', 'open_long'].includes(type.toLowerCase()) ? 'green' :
                                            ['sell', 'open_short'].includes(type.toLowerCase()) ? 'red' :
                                                ['close', 'close_long', 'close_short'].includes(type.toLowerCase()) ? 'orange' :
                                                    'default'
                                    }
                                >
                                    {type}
                                </Tag>
                            </Option>
                        ))}
                    </Select>
                </Col>

                {/* 合约过滤 */}
                <Col xs={24} sm={12} md={8} lg={6}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        合约代码
                    </Text>
                    <Select
                        mode="multiple"
                        placeholder="选择合约"
                        style={{ width: '100%' }}
                        value={filterParams.symbols || []}
                        onChange={(value) => handleFilterChange('symbols', value)}
                        maxTagCount={2}
                        allowClear
                    >
                        {filterOptions.symbols.map(symbol => (
                            <Option key={symbol} value={symbol}>
                                <Tag color="blue">{symbol}</Tag>
                            </Option>
                        ))}
                    </Select>
                </Col>

                {/* 执行状态过滤 */}
                <Col xs={24} sm={12} md={8} lg={6}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        执行状态
                    </Text>
                    <Select
                        mode="multiple"
                        placeholder="选择执行状态"
                        style={{ width: '100%' }}
                        value={filterParams.execution_status || []}
                        onChange={(value) => handleFilterChange('execution_status', value)}
                        maxTagCount={2}
                        allowClear
                    >
                        {filterOptions.executionStatuses.map(status => (
                            <Option key={status} value={status}>
                                <Tag
                                    color={
                                        status === 'Filled' ? 'success' :
                                            status === 'PartiallyFilled' ? 'warning' :
                                                status === 'Submitted' ? 'processing' :
                                                    status === 'Rejected' ? 'error' :
                                                        'default'
                                    }
                                >
                                    {status}
                                </Tag>
                            </Option>
                        ))}
                    </Select>
                </Col>

                {/* 最大显示条数 */}
                <Col xs={24} sm={12} md={8} lg={6}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        最大显示条数
                    </Text>
                    <Select
                        style={{ width: '100%' }}
                        value={filterParams.max_items || 200}
                        onChange={(value) => handleFilterChange('max_items', value)}
                    >
                        <Option value={50}>50 条</Option>
                        <Option value={100}>100 条</Option>
                        <Option value={200}>200 条</Option>
                        <Option value={500}>500 条</Option>
                        <Option value={1000}>1000 条</Option>
                    </Select>
                </Col>
            </Row>

            {/* 当前过滤条件摘要 */}
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
                <Text strong style={{ marginRight: 8 }}>当前过滤条件:</Text>
                <Space wrap>
                    {filterParams.time_range_hours && (
                        <Tag color="blue">
                            时间: 最近 {filterParams.time_range_hours} 小时
                        </Tag>
                    )}
                    {filterParams.strategy_names?.length && (
                        <Tag color="green">
                            策略: {filterParams.strategy_names.length} 个
                        </Tag>
                    )}
                    {filterParams.signal_types?.length && (
                        <Tag color="orange">
                            信号类型: {filterParams.signal_types.length} 个
                        </Tag>
                    )}
                    {filterParams.symbols?.length && (
                        <Tag color="purple">
                            合约: {filterParams.symbols.length} 个
                        </Tag>
                    )}
                    {filterParams.execution_status?.length && (
                        <Tag color="cyan">
                            状态: {filterParams.execution_status.length} 个
                        </Tag>
                    )}
                    {filterParams.max_items && (
                        <Tag color="default">
                            显示: {filterParams.max_items} 条
                        </Tag>
                    )}
                    {(!filterParams.time_range_hours &&
                        !filterParams.strategy_names?.length &&
                        !filterParams.signal_types?.length &&
                        !filterParams.symbols?.length &&
                        !filterParams.execution_status?.length) && (
                            <Tag color="default">
                                无过滤条件
                            </Tag>
                        )}
                </Space>
            </div>
        </Card>
    );
}; 