import axios from 'axios';
import { AllSettings, ConfigData, CTPTestResult } from '../types/settings';

const API_BASE_URL = '/api';

export class SettingsService {
    // 配置相关
    static async getConfig(): Promise<ConfigData> {
        const response = await axios.get(`${API_BASE_URL}/config/config`);
        return response.data;
    }

    static async saveConfig(configData: ConfigData): Promise<{ success: boolean; message: string }> {
        const response = await axios.post(`${API_BASE_URL}/config/config`, configData);
        return response.data;
    }

    static async getLoginInfo() {
        const response = await axios.get(`${API_BASE_URL}/config/login-info`);
        return response.data;
    }

    static async getCTPConfig() {
        const response = await axios.get(`${API_BASE_URL}/config/ctp-config`);
        return response.data;
    }

    // CTP连接测试
    static async testCTPConnection(ctpConfig: {
        trade_addr: string;
        quote_addr: string;
        broker: string;
        appid: string;
        auth_code: string;
    }): Promise<CTPTestResult> {
        const response = await axios.post(`${API_BASE_URL}/system/test-ctp`, ctpConfig);
        return response.data;
    }

    // 系统状态
    static async getSystemStatus() {
        const response = await axios.get(`${API_BASE_URL}/system/status`);
        return response.data;
    }

    static async stopCTP() {
        const response = await axios.post(`${API_BASE_URL}/system/stop-ctp`);
        return response.data;
    }

    // 应用设置（本地存储）
    static getAppSettings(): AllSettings {
        const defaultSettings: AllSettings = {
            system: {
                theme: 'light',
                autoRefresh: true,
                language: 'zh'
            },
            trading: {
                confirmTrade: true,
                soundAlert: false,
                riskLevel: 'medium'
            },
            security: {
                autoLogoutTime: 30,
                rememberLogin: false,
                twoFactorAuth: false
            },
            log: {
                logLevel: 'info',
                saveLog: true,
                maxLogSize: 100
            }
        };

        try {
            const saved = localStorage.getItem('appSettings');
            if (saved) {
                return { ...defaultSettings, ...JSON.parse(saved) };
            }
        } catch (error) {
            console.error('Failed to load app settings:', error);
        }

        return defaultSettings;
    }

    static saveAppSettings(settings: AllSettings): void {
        try {
            localStorage.setItem('appSettings', JSON.stringify(settings));
        } catch (error) {
            console.error('Failed to save app settings:', error);
            throw new Error('保存设置失败');
        }
    }

    // 重置设置
    static resetAppSettings(): void {
        localStorage.removeItem('appSettings');
    }

    // 导出设置
    static exportSettings(): string {
        const config = this.getAppSettings();
        return JSON.stringify(config, null, 2);
    }

    // 导入设置
    static importSettings(settingsJson: string): AllSettings {
        try {
            const settings = JSON.parse(settingsJson);
            this.saveAppSettings(settings);
            return settings;
        } catch (error) {
            throw new Error('导入设置失败：格式不正确');
        }
    }
} 