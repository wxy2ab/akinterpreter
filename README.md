# akinterpreter

**English** | [简体中文](./README.zh-CN.md)

![Project Logo](./docs/logo256.png)

akinterpreter is an LLM-powered financial market query and analysis tool. It uses data providers such as [akshare](https://akshare.akfamily.xyz/) and [tushare](https://tushare.pro/) to retrieve market data, generate analysis code, execute plans, and produce reports from natural-language requests.

## Features

- Query financial data with natural language instead of writing code.
- Automatically retrieve and analyze market data.
- Generate code, correct errors, and return usable results.
- Support multiple LLM providers.
- Use LLM APIs inside generated code for more advanced analysis.
- Run from the command line or through the web service.

## Data Providers

- [akshare](https://github.com/akfamily/akshare) is an open-source financial data toolkit with broad coverage across stocks, futures, options, bonds, indexes, funds, foreign exchange, macroeconomic data, and news.
- [tushare](https://tushare.pro/) is an optional paid data platform with more stable data quality. A tushare account and API token are required before it can be used.

## Installation

### Python Environment

```bash
git clone git@github.com:wxy2ab/akinterpreter.git
cd akinterpreter

# Optional: create an isolated environment
conda create -p ./env python=3.12
conda activate ./env

pip install -r requirements.txt
```

Create the local configuration file:

```bash
cp setting.ini.template setting.ini
```

On Windows:

```bat
copy setting.ini.template setting.ini
```

Update `setting.ini` with the LLM provider and API key you want to use.

### Packaged Installation

If you do not have a Python environment:

1. Download a release archive and extract it to a path without non-ASCII characters.
2. Rename `setting.ini.template` to `setting.ini`.
3. Set `llm_api` and the matching API key in `setting.ini`.
4. Run `run.bat` on Windows or `chmod +x ./run.sh && ./run.sh` on Linux and macOS.

## Running

Start the CLI:

```bash
python cli.py
```

Start the web service:

```bash
python main.py
```

The first web-service startup may take longer while local data is prepared.

## Configuration

The main settings are defined in `setting.ini`:

```ini
[Default]
llm_api = DeepSeekClient
llm_cheap_api = CheapClaude
embedding_api = MiniMaxEmbedding
ranker_api = BaiduBCEReranker
talker = CliTalker
tushare_key =
OPENAI_API_KEY =
deep_seek_api_key =
DASHSCOPE_API_KEY =
glm_api_key =
```

See [`setting.ini.template`](./setting.ini.template) for the full list of provider-specific options.

## Supported LLM APIs

The project includes clients for multiple providers, including:

| Client | Provider | Main dependency |
| --- | --- | --- |
| `SimpleClaudeAwsClient` | AWS Bedrock Claude | `anthropic` |
| `SimpleAzureClient` | Azure OpenAI | `openai` |
| `DeepSeekClient` | DeepSeek | `openai` |
| `QianWenClient` | Alibaba Cloud Qwen | `dashscope` |
| `MoonShotClient` | Moonshot | `openai` |
| `GLMClient` | Zhipu GLM | `zhipuai` |
| `DoubaoApiClient` | Volcengine Doubao | Volcengine SDK |
| `GeminiAPIClient` | Google Gemini | Google Cloud SDK |
| `HunyuanClient` | Tencent Hunyuan | Tencent Cloud SDK |
| `MiniMaxClient` | MiniMax | built-in HTTP client |
| `OpenAIClient` | OpenAI | `openai` |

Additional provider implementations live in [`core/llms`](./core/llms).

## Basic Workflow

1. Submit a request such as:

   ```text
   Analyze the Shanghai Composite Index trend for this year.
   ```

2. Review the generated execution plan.
3. Add, remove, or revise steps as needed.
4. Run the plan.
5. Export generated code when useful.

## Commands

Commands become available after the first data query:

| Command | Description |
| --- | --- |
| `help` | Show help |
| `clear_history` | Clear chat history |
| `export` | Export generated code |
| `go` | Execute the current plan |
| `modify_step_code=step_number query` | Modify the generated code for a step |
| `redo` | Run the plan again without regenerating code |

## Security Notice

- This project can execute generated code and currently does not run that code in a sandbox. Use it only if you understand the risks.
- Public financial data APIs may be delayed or inaccurate.
- LLM-generated reports can contain mistakes and are not professional financial advice.
- The authors provide a code-generation and analysis tool, not investment advice or guarantees.

## Limitations

- Free APIs have data-quality, rate-limit, and timeliness constraints.
- Some LLM provider integrations have not been tested equally.
- Prompt design and model parameters may require adjustment for your use case.
- The project is evolving, and some features remain incomplete.

## Related Projects

- [akshare](https://github.com/akfamily/akshare)
- [tushare](https://tushare.pro/)
- [ak_code_library](https://github.com/wxy2ab/ak_code_library)
- [llm_dealer](https://github.com/wxy2ab/llm_dealer)

## Contributing

Issues and pull requests are welcome. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the current contribution guide.
