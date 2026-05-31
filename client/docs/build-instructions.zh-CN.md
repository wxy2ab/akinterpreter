# Web 前端构建说明

[English](./build-instructions.md) | **简体中文**

本文档详细说明如何构建Web前端应用。

## 📋 环境要求

### Node.js环境
- **Node.js**: >= 18.0.0 (推荐使用 18.17.0 或更高版本)
- **npm**: >= 9.0.0 (或使用 yarn >= 1.22.0)

### 系统要求
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+ 或同等版本)
- **内存**: 至少 4GB RAM (推荐 8GB+)
- **磁盘空间**: 至少 2GB 可用空间

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入前端目录
cd client

# 安装依赖 (使用npm)
npm install

# 或使用yarn
yarn install
```

### 2. 开发模式运行

```bash
# 启动开发服务器
npm run dev

# 或使用yarn
yarn dev
```

开发服务器将在 `http://localhost:3000` 启动。

### 3. 构建生产版本

```bash
# 构建生产版本
npm run build

# 或使用yarn
yarn build
```

构建完成后，文件将输出到 `../build/` 目录。

## 📁 构建输出

构建完成后的目录结构：

```
./build/                    # 构建输出根目录
├── index.html             # 主HTML文件
├── assets/                # 静态资源
│   ├── css/              # CSS文件
│   ├── js/               # JavaScript文件
│   ├── images/           # 图片资源
│   └── fonts/            # 字体文件
├── favicon.ico           # 网站图标
└── manifest.json         # PWA配置文件
```

## 🔧 构建配置

### Vite配置 (vite.config.ts)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  
  // 构建配置
  build: {
    outDir: '../build',              // 输出到项目根目录的build文件夹
    emptyOutDir: true,              // 构建前清空输出目录
    sourcemap: false,               // 生产环境不生成sourcemap
    minify: 'esbuild',              // 使用esbuild压缩
    target: 'es2015',               // 目标浏览器版本
    
    // 分包策略
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd'],
          redux: ['@reduxjs/toolkit', 'react-redux'],
          socketio: ['socket.io-client']
        }
      }
    },
    
    // 资源处理
    assetsDir: 'assets',
    assetsInlineLimit: 4096,        // 小于4KB的资源内联
  },
  
  // 开发服务器配置
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  },
  
  // 路径别名
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils')
    }
  }
})
```

### TypeScript配置 (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@store/*": ["./src/store/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@utils/*": ["./src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 📦 构建脚本说明

### package.json 脚本

```json
{
  "scripts": {
    "dev": "vite",                          // 开发模式
    "build": "tsc && vite build",           // 构建生产版本
    "build:dev": "vite build --mode development", // 构建开发版本
    "preview": "vite preview",              // 预览构建结果
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "type-check": "tsc --noEmit",          // 类型检查
    "clean": "rimraf ../build",             // 清理构建目录
    "analyze": "npm run build && npx vite-bundle-analyzer ../build/stats.html"
  }
}
```

### 构建命令详解

1. **开发构建**
   ```bash
   npm run build:dev
   ```
   - 保留sourcemap
   - 不压缩代码
   - 用于调试生产问题

2. **生产构建**
   ```bash
   npm run build
   ```
   - 代码压缩和优化
   - 移除调试信息
   - 生成最小化bundle

3. **类型检查**
   ```bash
   npm run type-check
   ```
   - 仅进行TypeScript类型检查
   - 不生成文件

4. **代码分析**
   ```bash
   npm run analyze
   ```
   - 分析bundle大小
   - 生成可视化报告

## 🎯 构建优化

### 1. 代码分割
- **按路由分割**: 使用React.lazy()懒加载页面组件
- **按功能分割**: 将第三方库单独打包
- **按大小分割**: 大文件自动分割

### 2. 资源优化
- **图片压缩**: 自动压缩图片资源
- **字体优化**: 仅包含使用的字符
- **CSS优化**: 移除未使用的样式

### 3. 缓存策略
```typescript
// vite.config.ts 中的缓存配置
build: {
  rollupOptions: {
    output: {
      // 文件名包含hash，便于缓存
      entryFileNames: 'assets/js/[name].[hash].js',
      chunkFileNames: 'assets/js/[name].[hash].js',
      assetFileNames: 'assets/[ext]/[name].[hash].[ext]'
    }
  }
}
```

## 🔍 构建验证

### 1. 构建完整性检查
```bash
# 检查构建输出
ls -la ../build/

# 验证主要文件存在
test -f ../build/index.html && echo "✅ index.html exists"
test -d ../build/assets && echo "✅ assets directory exists"
```

### 2. 构建大小分析
```bash
# 查看构建文件大小
du -sh ../build/*

# 详细分析
npm run analyze
```

### 3. 功能测试
```bash
# 本地预览构建结果
npm run preview

# 访问 http://localhost:4173 测试功能
```

## 🚨 常见问题

### 1. 构建失败

**问题**: `npm run build` 失败
```
Error: Cannot resolve module
```

**解决方案**:
```bash
# 清理node_modules和重新安装
rm -rf node_modules package-lock.json
npm install

# 或清理缓存
npm cache clean --force
```

### 2. 内存不足

**问题**: 构建时内存溢出
```
JavaScript heap out of memory
```

**解决方案**:
```bash
# 增加Node.js内存限制
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### 3. 路径问题

**问题**: 构建后资源路径错误

**解决方案**: 检查vite.config.ts中的base配置
```typescript
export default defineConfig({
  base: './',  // 使用相对路径
  // ...
})
```

### 4. TypeScript错误

**问题**: 类型检查失败

**解决方案**:
```bash
# 仅构建，跳过类型检查
npx vite build --skipLibCheck

# 或修复类型错误
npm run type-check
```

## 📈 性能优化建议

### 1. 构建性能
- 使用多核CPU并行构建
- 启用增量构建
- 合理配置缓存

### 2. 运行时性能
- 启用代码分割
- 使用CDN加速
- 启用Gzip压缩

### 3. 开发体验
- 使用热重载
- 配置代理服务器
- 启用sourcemap

## 📚 相关文档

- [Vite官方文档](https://vitejs.dev/)
- [React官方文档](https://react.dev/)
- [TypeScript官方文档](https://www.typescriptlang.org/)
- [Ant Design文档](https://ant.design/)

---

> 💡 **提示**: 如果遇到构建问题，请先查看本文档的常见问题部分，或查看项目的GitHub Issues。 
