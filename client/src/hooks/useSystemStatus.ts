import { useCallback, useEffect } from 'react';
import { useDispatch } from 'react-redux';

import { setError, updateSystemStatus } from '../store/slices/systemSlice';

export const useSystemStatus = () => {
    const dispatch = useDispatch();

    const fetchSystemStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/system/status');
            if (response.ok) {
                const data = await response.json();
                dispatch(updateSystemStatus(data));
            } else {
                console.error('获取系统状态失败:', response.status);
                dispatch(setError('获取系统状态失败'));
            }
        } catch (error) {
            console.error('获取系统状态异常:', error);
            dispatch(setError('获取系统状态异常'));
        }
    }, [dispatch]);

    useEffect(() => {
        // 立即获取一次状态
        fetchSystemStatus();

        // 每5秒更新一次状态
        const interval = setInterval(fetchSystemStatus, 5000);

        return () => clearInterval(interval);
    }, [fetchSystemStatus]);

    return {
        fetchSystemStatus,
    };
}; 