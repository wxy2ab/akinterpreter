---
title: akinterpreter
---

**English** | [简体中文](./page.zh-CN.md)

akinterpreter is a free and open-source financial market query and analysis tool released under the MIT License. Contributions are welcome. {% .lead %}

{% quick-links %}

{% quick-link title="Installation" icon="installation" href="/docs/non_python_install" description="Install akinterpreter." /%}

{% quick-link title="Configuration" icon="presets" href="/docs/select_llm_api" description="Configure an LLM provider." /%}

{% quick-link title="Usage" icon="plugins" href="/docs/instruction" description="Use the CLI and web service." /%}

{% quick-link title="Tips" icon="theming" href="/docs/use_outside" description="Use remote LLM APIs." /%}

{% /quick-links %}

---

## Quick Start

```bash
git clone git@github.com:wxy2ab/akinterpreter.git
cd akinterpreter
conda create -p ./env python=3.12
conda activate ./env
pip install -r requirements.txt
python cli.py
```

{% callout type="warning" title="Early-stage project" %}
akinterpreter is under active development. Please report reproducible bugs through [GitHub Issues](https://github.com/wxy2ab/akinterpreter/issues).
{% /callout %}

## Web Service

```bash
python main.py
```

Open `http://localhost:8181/`.

## Example Query

```text
Analyze the gold futures trend for this year.
```

## Using tushare

Install `tushare`, then set `tushare_key` in `setting.ini`. Register at [tushare.pro](https://tushare.pro/register).
