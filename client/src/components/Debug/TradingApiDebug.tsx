import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Typography, Row, Col, Badge, Alert } from 'antd';
import { ReloadOutlined, BugOutlined, ApiOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface ApiTestResult {
  url: string;
  name: string;
  label: string;
  status?: number;
  success: boolean;
  data?: any;
  error?: string;
  timestamp: string;
}

const TradingApiDebug: React.FC = () => {
  const [testResults, setTestResults] = useState<ApiTestResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [ctpStatus, setCtpStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  const apis = [
    { url: '/api/trading-management/ctp-service-status', name: 'ctp_service', label: 'CTP服务状态' },
    { url: '/api/trading-management/positions', name: 'positions', label: '持仓数据' },
    { url: '/api/trading-management/orders', name: 'orders', label: '订单数据' },
    { url: '/api/trading-management/account', name: 'account', label: '账户信息' },
    { url: '/api/trading-management/status', name: 'status', label: '交易状态' },
    { url: '/api/trading-management/statistics', name: 'statistics', label: '交易统计' },
    { url: '/api/trading-management/ctp-status', name: 'ctp_status', label: 'CTP详细状态' }
  ];

  const checkCtpStatus = async () => {
    try {
      const response = await fetch('/api/trading-management/ctp-service-status');
      const result = await response.json();
      setCtpStatus(result.success && result.ctp_available ? 'online' : 'offline');
    } catch (error) {
      setCtpStatus('offline');
    }
  };

  const testSingleApi = async (api: typeof apis[0]): Promise<ApiTestResult> => {
    const timestamp = new Date().toLocaleTimeString();
    try {
      const response = await fetch(api.url);
      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }

      return {
        ...api,
        status: response.status,
        success: response.ok,
        data: data,
        timestamp
      };
    } catch (error) {
      return {
        ...api,
        success: false,
        error: error instanceof Error ? error.message : '未知错误',
        timestamp
      };
    }
  };

  const testAllApis = async () => {
    setIsLoading(true);
    const results: ApiTestResult[] = [];
    
    for (const api of apis) {
      const result = await testSingleApi(api);
      results.push(result);
      setTestResults([...results]);
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    setIsLoading(false);
  };

  useEffect(() => {
    checkCtpStatus();
    const interval = setInterval(checkCtpStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const renderApiResult = (result: ApiTestResult) => (
    <Card 
      key={result.name}
      size="small" 
      title={
        <Space>
          <Badge 
            status={result.success ? 'success' : 'error'} 
            text={result.label}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {result.timestamp}
          </Text>
        </Space>
      }
      style={{ marginBottom: 8 }}
    >
      <div style={{ marginBottom: 8 }}>
        <Text strong>URL: </Text>
        <Text code>{result.url}</Text>
      </div>
      
      {result.status && (
        <div style={{ marginBottom: 8 }}>
          <Text strong>状态码: </Text>
          <Badge 
            status={result.success ? 'success' : 'error'} 
            text={result.status.toString()}
          />
        </div>
      )}

      {result.error && (
                 <Alert 
           message="错误信息" 
           description={result.error}
           type="error" 
           showIcon 
           style={{ marginBottom: 8 }}
         />
      )}

      {result.data && (
        <div>
          <Text strong>响应数据:</Text>
          <pre style={{ 
            background: '#f5f5f5', 
            padding: 8, 
            borderRadius: 4, 
            fontSize: '12px',
            maxHeight: '200px',
            overflow: 'auto',
            marginTop: 4
          }}>
            {JSON.stringify(result.data, null, 2)}
          </pre>
        </div>
      )}
    </Card>
  );

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={24}>
        <Col span={24}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <Title level={2} style={{ margin: 0 }}>
                  <BugOutlined /> 交易API诊断工具
                </Title>
                <Paragraph type="secondary">
                  诊断交易管理API的连接状态和数据可用性
                </Paragraph>
              </div>
              <Space>
                <Badge 
                  status={ctpStatus === 'online' ? 'processing' : 'error'} 
                  text={ctpStatus === 'online' ? 'CTP已连接' : 'CTP未连接'}
                />
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={checkCtpStatus}
                  loading={ctpStatus === 'checking'}
                >
                  检查CTP状态
                </Button>
              </Space>
            </div>

            <Space size="middle" style={{ marginBottom: 24 }}>
              <Button 
                type="primary" 
                icon={<ApiOutlined />}
                onClick={testAllApis}
                loading={isLoading}
              >
                测试所有API
              </Button>
              <Button 
                icon={<ReloadOutlined />}
                onClick={() => window.location.reload()}
              >
                刷新页面
              </Button>
              <Button onClick={() => setTestResults([])}>
                清空结果
              </Button>
            </Space>

            {testResults.length === 0 && !isLoading && (
              <Alert
                message="准备就绪"
                description="点击'测试所有API'开始诊断..."
                type="info"
                showIcon
              />
            )}

            {testResults.length > 0 && (
              <div>
                <Title level={4}>测试结果</Title>
                {testResults.map(renderApiResult)}
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={24} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="页面路由测试">
            <Space direction="vertical">
              <div>
                <Text strong>React路由测试:</Text>
                <div style={{ marginTop: 8 }}>
                  <Space wrap>
                    <Button size="small" onClick={() => window.open('/trading-management', '_blank')}>
                      交易管理页面
                    </Button>
                    <Button size="small" onClick={() => window.open('/trading-management-optimized', '_blank')}>
                      优化版交易管理
                    </Button>
                    <Button size="small" onClick={() => window.open('/dashboard', '_blank')}>
                      仪表板页面
                    </Button>
                    <Button size="small" onClick={() => window.open('/', '_blank')}>
                      主页
                    </Button>
                  </Space>
                </div>
              </div>
              
              <Alert
                message="诊断建议"
                description={
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    <li>如果主页和仪表板正常，但交易管理页面白屏，说明是TradingPanel组件的问题</li>
                    <li>如果所有页面都白屏，说明是前端构建或路由的问题</li>
                    <li>如果API测试都返回错误，说明是后端API的问题</li>
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

export default TradingApiDebug; 