import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],

    // 构建配置
    build: {
        // client sits directly under the project root in this repository.
        outDir: '../build',
        // 清空输出目录
        emptyOutDir: true,
        // 生成 source map
        sourcemap: true,
        // 优化配置
        rollupOptions: {
            output: {
                // 分块策略
                manualChunks: {
                    vendor: ['react', 'react-dom'],
                    antd: ['antd'],
                    redux: ['@reduxjs/toolkit', 'react-redux'],
                    router: ['react-router-dom'],
                    socket: ['socket.io-client'],
                    charts: ['recharts']
                }
            }
        }
    },

    // 开发服务器配置
    server: {
        port: 3000,
        open: true,
        // 代理API请求到后端服务器
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            },
            '/socket.io': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                ws: true
            }
        }
    },

    // 路径别名配置
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
            '@components': resolve(__dirname, 'src/components'),
            '@store': resolve(__dirname, 'src/store'),
            '@services': resolve(__dirname, 'src/services'),
            '@utils': resolve(__dirname, 'src/utils'),
            '@hooks': resolve(__dirname, 'src/hooks')
        }
    },

    // 预览服务器配置
    preview: {
        port: 3001,
        open: true
    }
}) 
