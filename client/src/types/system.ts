// 系统状态相关类型定义

export interface SystemStatus {
    server_time: string;
    ctp_connected: boolean;
    web_bridge_running: boolean;
    trading_day: string | null;
    active_connections: number;
    // 🔧 新增：详细的连接状态分析
    ctp_status_analysis?: CTPStatusAnalysis;
    web_bridge_details?: WebBridgeDetails;
    display_status?: DisplayStatus;
}

export interface ConnectionStatus {
    trade: string;
    quote: string;
    connected: boolean;
}

// 🔧 新增：详细的CTP状态分析
export interface CTPStatusAnalysis {
    overall_status: string;
    status_description: string;
    status_level: 'success' | 'warning' | 'error' | 'info';
    trade_connection: ConnectionDetail;
    quote_connection: ConnectionDetail;
    trading_time_info: TradingTimeInfo;
    detailed_info: DetailedInfo;
}

export interface ConnectionDetail {
    status: string;
    status_name: string;
    raw_status: string;
    connection_type: string;
}

export interface TradingTimeInfo {
    is_trading_time: boolean;
    current_time: string;
    current_date: string;
    weekday: number;
    is_weekend: boolean;
    next_trading_session?: NextTradingSession;
    symbol_category: string;
}

export interface NextTradingSession {
    start_time: string;
    end_time: string;
    date: string;
}

export interface DetailedInfo {
    is_ctp_running: boolean;
    is_trading_time: boolean;
    current_time: string;
    current_date: string;
    next_trading_session?: NextTradingSession;
    analysis_timestamp: string;
    error_message?: string;
}

export interface WebBridgeDetails {
    events_processed: number;
    uptime_seconds: number;
    websocket_connections: number;
    error?: string;
}

// 🔧 新增：前端显示状态
export interface DisplayStatus {
    connection_status: string;
    status_description: string;
    status_level: 'success' | 'warning' | 'error' | 'info';
    is_trading_time: boolean;
    current_time: string;
    next_trading_session?: NextTradingSession;
} 