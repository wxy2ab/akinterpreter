---
title: Configure API Keys
nextjs:
  metadata:
    title: Configure API Keys
    description: Configure provider-specific API keys.
---

**English** | [简体中文](./page.zh-CN.md)

Only configure the keys required by your selected provider.

```ini
[Default]
llm_api = DeepSeekClient
llm_cheap_api = CheapClaude
embedding_api = BGELargeZhAPI
ranker_api = BaiduBCEReranker
talker = CliTalker

project_id =
aws_access_key_id =
aws_secret_access_key =
tushare_key =
AZURE_OPENAI_API_KEY =
AZURE_OPENAI_ENDPOINT =
glm_api_key =
deep_seek_api_key =
moonshot_api_key =
DASHSCOPE_API_KEY =
baichuan_api_key =
volcengine_api_key =
minimax_api_key =
OPENAI_API_KEY =
hunyuan_SecretId =
hunyuan_SecretKey =
```

For example, when using DeepSeek, set `llm_api = DeepSeekClient` and fill in `deep_seek_api_key`.

