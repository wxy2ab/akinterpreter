# akinterpreter 使用akshare的金融市场查询和分析工具

![Project Logo](./docs/logo256.png)

## 介绍
[akshare](https://akshare.akfamily.xyz/) 是一个开源数据工具([github地址](https://github.com/akfamily/akshare]))，里面有900多个函数，可以查询国内外的各种金融数据，包括股票，期货，期权，债券，指数，基金，外汇，宏观经济，新闻，美股，港股等等各类数据。目前持续活跃，保持高频次的更新。
如果不想花钱，想利用API查询和分析数据，那么akshare是非常好的选择。
本项目就是利用LLM的API，基于akshare搭建解释器，只要你会搭建python环境，就可以用自然语言快速完成一些查询和分析。

## 特性
- 自然语言查询，不用写代码
- 自行更正代码，输出有效结果
- 支持多种 LLM API

## 安装指南

```bash
# 克隆项目
git clone git@github.com:wxy2ab/akinterpreter.git

# 进入项目目录
cd akinterpreter

# 安装依赖
npm install -r requirments.txt

# 启动cli
python cli.py

# 启动web
python main.py
```

## 修改配置-配置模板
```text
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
GAODE_MAP_API_KEY = 
OPEN_WEATHER_API_KEY = 
ERNIE_API_KEY = 
ERNIE_SERCRET_KEY =
glm_api_key = 
deep_seek_api_key = 
moonshot_api_key = 
DASHSCOPE_API_KEY =
baichuan_api_key =
volcengine_api_key = 
volcengine_embedding = 
volcengine_doubao = 
```

## 如何填写
- **llm_api**  可选值,除了填写 api_key, 还需要安装依赖项 , 申请 api_key 的时候，应该都知道安装什么依赖项
    * **SimpleClaudeAwsClient**:  Aws的 Claude API ，国内可用，依赖 Anthopic 库
    * **SimpleAzureClient**:  Azure的 OpenAI API，国内可用，依赖 openai 库
    * **DeepSeekClient**:  DeepSeek的 API (依赖openai库)
    * **QianWenClient**: 同义千问的 API (还没测试,依赖dashscope库)
    * **MoonShotClient**: MooonShot的 API (还没测试,依赖openai库)
    * **GLMClient**: 智谱的GLM API (还没测试,依赖 zhipuai库)
    * **ErnieApiClient**: 百度文心一言的 API (还没测试，无依赖)
    * **DoubaoApiClient**: 字节的火山引擎 豆包 API (还没测试，依赖火山 SDK)
    * **GeminiAPIClient**: Google 的 Gemini API (国内不可用，依赖 google cloud 库)
- llm_cheap_api 用于处理简易 NLP 任务，暂时不用填
- embedding_api 用于文本向量化，暂时不用填
- ranker_api 用于二次排序，暂时不用填
- talker = CliTalker  要用cli模式,就不要动这个 
- 后面的 api_key , 不同都填，选择哪个 LLM API，就填哪个 api_key

## 安全说明
- ⚠️代码中含有执行任意代码的功能，并且目前不在沙盒中运行。还拥有生成代码的的功能，理论上说，有可能生成对你的电脑产生危害。如果你不知道自己在做什么，请不要使用本项目。
- ⚠️akshare 的 api 基本来自公开数据，可能有滞后性，甚至可能未必准确
- ⚠️LLM API 生成的报告未必准确，且未必专业，仅供参考，批判使用
- ⚠️作者只提供一个代码生成工具，不提供任何保证，也不提供投资建议和咨询。如果使用者依据数据和代码结果为依据进行投资，风险自负。