---
title: Installation
nextjs:
  metadata:
    title: Installation
    description: Recommended installation steps for Python users.
---

**English** | [简体中文](./page.zh-CN.md)

Installing from source is recommended if you already have a Python environment.

## Install

```bash
git clone git@github.com:wxy2ab/akinterpreter.git
cd akinterpreter

conda create -p ./env python=3.12
conda activate ./env

pip install -r requirements.txt
cp setting.ini.template setting.ini
```

Update `setting.ini`, then start the CLI or web service:

```bash
python cli.py
python main.py
```

See [LLM API configuration](../select_llm_api) for provider settings.

