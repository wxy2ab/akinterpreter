---
title: Install Without a Python Environment
nextjs:
  metadata:
    title: Install Without a Python Environment
    description: Install a packaged akinterpreter release.
---

**English** | [简体中文](./page.zh-CN.md)

## Download a Release

Download a ZIP archive from [GitHub Releases](https://github.com/wxy2ab/akinterpreter/releases).

## Extract the Archive

Extract the archive to a directory with enough free space. Prefer a path without non-ASCII characters because environment setup tools may fail on some systems.

## Configure `setting.ini`

Rename `setting.ini.template` to `setting.ini`, then select an LLM provider and add the matching API key.

## Run

On Windows:

```bat
run.bat
```

On Linux and macOS:

```bash
chmod +x ./run.sh
./run.sh
```

The first run may take longer because it installs the Python environment and dependencies. Open `http://localhost:8181` after startup.
