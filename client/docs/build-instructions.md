# Web Client Build Guide

**English** | [简体中文](./build-instructions.zh-CN.md)

## Requirements

- Node.js `>= 18`
- npm `>= 9`
- At least 4 GB of RAM

## Install Dependencies

```bash
cd client
npm install
```

## Development Server

```bash
npm run dev
```

The Vite development server starts at `http://localhost:3000`.

## Production Build

```bash
npm run build
```

The build output is written to `../build/`.

```text
build/
├── index.html
└── assets/
```

## Preview the Build

```bash
npm run preview
```

The preview server starts at `http://localhost:3001`.

## Type Checking

```bash
npx tsc --noEmit
```

## Configuration Notes

The Vite configuration lives in [`../vite.config.ts`](../vite.config.ts).

- API requests under `/api` are proxied to `http://localhost:8000`.
- Socket.IO requests under `/socket.io` are proxied to the same backend.
- Production assets are emitted to the repository-level `build/` directory.

## Troubleshooting

### Dependency Errors

```bash
rm -rf node_modules
npm install
```

### Node.js Memory Errors

```bash
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### Verify Build Artifacts

```bash
test -f ../build/index.html
test -d ../build/assets
```

## References

- [Vite](https://vitejs.dev/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Ant Design](https://ant.design/)

