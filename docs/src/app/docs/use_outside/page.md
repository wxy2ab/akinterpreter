---
title: Using Remote LLM APIs
nextjs:
  metadata:
    title: Using Remote LLM APIs
    description: Configure Azure OpenAI or a network proxy.
---

**English** | [简体中文](./page.zh-CN.md)

Some LLM APIs may not be directly reachable from your network.

## Use `SimpleAzureClient`

Azure OpenAI can be used through `SimpleAzureClient`. Create an Azure OpenAI deployment and configure the matching endpoint and API key in `setting.ini`.

## Configure a Proxy

If your environment uses an HTTP proxy, initialize it before making remote API requests:

```python
from core.utils.tsdata import check_proxy_running

check_proxy_running("127.0.0.1", 10809, "http")
```

