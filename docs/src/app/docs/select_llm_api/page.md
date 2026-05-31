---
title: Configure llm_api
nextjs:
  metadata:
    title: Configure llm_api
    description: Select an LLM provider.
---

**English** | [简体中文](./page.zh-CN.md)

akinterpreter supports multiple LLM providers. Select a client class and configure the matching API key.

## Example

Copy the configuration template:

```bash
cp setting.ini.template setting.ini
```

Then update the provider:

```ini
[Default]
llm_api = SimpleDeepSeekClient
llm_cheap_api = CheapMiniMax
embedding_api = MiniMaxEmbedding
ranker_api = BaiduBCEReranker
talker = CliTalker
```

## Common Providers

| Client | Provider | Dependency |
| --- | --- | --- |
| `SimpleClaudeAwsClient` | AWS Bedrock Claude | `anthropic` |
| `SimpleAzureClient` | Azure OpenAI | `openai` |
| `SimpleDeepSeekClient` | DeepSeek | `openai` |
| `QianWenClient` | Alibaba Cloud Qwen | `dashscope` |
| `MoonShotClient` | Moonshot | `openai` |
| `GLMClient` | Zhipu GLM | `zhipuai` |
| `GeminiAPIClient` | Google Gemini | Google Cloud SDK |
| `HunyuanClient` | Tencent Hunyuan | Tencent Cloud SDK |

Additional implementations are available under `core/llms`.

## Recommendations

- `SimpleDeepSeekClient` is easy to configure and inexpensive.
- `SimpleClaudeAwsClient` is a strong choice for code generation if you have AWS Bedrock access.
- Use `llm_cheap_api` for low-cost text-processing tasks.
