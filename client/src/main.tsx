import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

console.log('main.tsx 正在执行...');

const rootElement = document.getElementById('root');
console.log('Root element:', rootElement);

if (rootElement) {
    const root = ReactDOM.createRoot(rootElement);
    console.log('创建 React root 成功');

    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );

    console.log('React 应用渲染完成');
} else {
    console.error('找不到 root 元素！');
} 