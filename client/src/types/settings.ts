// 设置页面相关类型定义

export interface LoginInfo {
    investor: string;
    password: string;
}

export interface CTPConfig {
    trade_addr: string;
    quote_addr: string;
    broker: string;
    appid: string;
    auth_code: string;
    simnow_symbol: string;
}

export interface ConfigData {
    login: LoginInfo;
    ctp: CTPConfig;
}

export interface SystemSettings {
    theme: 'light' | 'dark';
    autoRefresh: boolean;
    language: 'zh' | 'en';
}

export interface TradingSettings {
    confirmTrade: boolean;
    soundAlert: boolean;
    riskLevel: 'low' | 'medium' | 'high';
}

export interface SecuritySettings {
    autoLogoutTime: number; // 分钟
    rememberLogin: boolean;
    twoFactorAuth: boolean;
}

export interface LogSettings {
    logLevel: 'debug' | 'info' | 'warning' | 'error';
    saveLog: boolean;
    maxLogSize: number; // MB
}

export interface AllSettings {
    system: SystemSettings;
    trading: TradingSettings;
    security: SecuritySettings;
    log: LogSettings;
}

export interface CTPTestResult {
    success: boolean;
    message: string;
    details?: {
        trade_server: string;
        quote_server: string;
        broker_id: string;
    };
} 