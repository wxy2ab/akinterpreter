# akinterpreter 使用akshare tushare的金融市场查询和分析工具

![Project Logo](./docs/logo256.png)

## 介绍
- [akshare](https://akshare.akfamily.xyz/) 是一个开源数据工具([github地址](https://github.com/akfamily/akshare))，里面有900多个函数，可以查询国内外的各种金融数据，包括股票，期货，期权，债券，指数，基金，外汇，宏观经济，新闻，美股，港股等等各类数据。目前持续活跃，保持高频次的更新。如果不想花钱，想利用API查询和分析数据，那么akshare是非常好的选择。    
- [tushare](https://tushare.pro/) 是一个性能更好，数据质量更稳定的数据平台。只需要一点费用，就能访问这些高质量数据。是目前最具性价比的金融数据平台。可以可靠的获取分钟数据。以及质量更好的新闻和研报数据。使用tushare需要先去网站注册key，并开通权限，否则无法使用。    
- 本项目是利用LLM的API，搭建的**解释器**，可以帮你写代码，获取数据，分析数据。只要简单的配置，就可以用自然语言快速完成查询和分析。

## 特性
- 自然语言查询，不用写代码
- 自动查数据，自动分析数据，降低数据分析难度
- 自行更正代码，输出有效结果
- 支持多种 LLM API
- 可以在生成的代码中继续使用LLM API，极大提升分析能力

## 安装指南

### 推荐安装方案
```bash
# 克隆项目
git clone git@github.com:wxy2ab/akinterpreter.git

# 进入项目目录
cd akinterpreter

# 可选，创建虚拟环境
conda create -p ./env python=3.12

# 激活虚拟环境
conda activate ./env

# 安装依赖
pip install -r requirments.txt

# 启动cli
python cli.py

# 启动web，首次运行需要准备数据，会慢一些
python main.py
```

### 没有python环境的安装方案
- **下载release版本**  
解压到任意目录,目录不要包含中文  
- **获得setting.ini**  
把setting.ini.template 修改为 ***setting.ini***  
- **配置llm_api**   
修改setting.ini中的***llm_api***，改成你需要的LLM API  ,取值参考后面的支持的LLM API列表  
- **添加api_key**   
修改setting.ini中的   对应你的llm api的api_key  
- **windows环境:**  
执行 **run.bat**  
- **linux & mac:**   
执行 chmod +x ./run.sh  &&  ./run.sh  
- **windows更新**   
执行 **update.bat**   
- **linux & mac更新**   
执行chmod +x ./update.sh  &&  ./update.sh  

## 生成配置文件
windows:
```shell
copy setting.ini.template setting.ini
```

linux & mac:
```bash
cp setting.ini.template setting.ini
```

## 修改配置-配置模板
```text
[Default]
llm_api = DeepSeekClient        #主要使用的LLM API，取值看下面的列表。需要自己申请key，并配置KEY
llm_cheap_api = CheapClaude     #处理简单NLP任务，建议使用CheapMiniMax(目前赠送1亿tokens) ,需要配置对应API KEY
embedding_api = MiniMaxEmbedding   #文本向量化用，如果你注册了MiniMax，那个建议使用MiniMax的embedding
ranker_api = BaiduBCEReranker   #二次排序用，暂时没有使用
talker = CliTalker              #不要改动
project_id =                    #Google gemini API 需要的proect id，非gemini API不用管
aws_access_key_id =             #AWS bedrock API 需要的key，非aws API不用管
aws_secret_access_key =         #AWS bedrock API 需要的key，非aws API不用管
tushare_key =                   #tushare API 需要的key  不用填
AZURE_OPENAI_API_KEY =          #Azure OpenAI API 需要的key，非azure API不用管
AZURE_OPENAI_ENDPOINT =         #Azure OpenAI API 需要的endpoint，非azure API不用管
GAODE_MAP_API_KEY =             #高德地图API 需要的key，不用管
OPEN_WEATHER_API_KEY =          #OpenWeatherMap API 需要的key，不用管
ERNIE_API_KEY =                 #百度文心一言API 需要的key，非百度API不用管
ERNIE_SERCRET_KEY =             #百度文心一言API 需要的key，非百度API不用管
glm_api_key =                   #智谱的GLM API 需要的key，非智谱API不用管
deep_seek_api_key =             #DeepSeek API 需要的key，非DeepSeekAPI不用管
moonshot_api_key =              #MooonShot API 需要的key，非MooonShotAPI不用管
DASHSCOPE_API_KEY =             #dashscope API 需要的key，非dashscopeAPI不用管
baichuan_api_key =              #百川API 需要的key，非百川API不用管
volcengine_api_key =            #火山引擎API 需要的key，非火山引擎API不用管
volcengine_embedding =          #火山引擎API 需要的key，非火山引擎API不用管
volcengine_doubao =             #火山引擎API 需要的key，非火山引擎API不用管
minimax_api_key =               #上海稀宇科技的API 需要的key，非上海稀宇科技的API不用管
zero_one_api_key =              #零一API 需要的key，非零一API不用管
OPENAI_API_KEY =                #OPENAI API 需要的key，非OPENAIAPI不用管
hunyuan_SecretId =              #腾讯混元API 需要的key，非腾讯混元API不用管
hunyuan_SecretKey =             #腾讯混元API 需要的key，非腾讯混元API不用管
```

## 支持的LLM API列表

| 类名                  | 厂商                        | 依赖       |
|----------------------|-----------------------------|------------|
| SimpleClaudeAwsClient| Aws bedrock部署的Claude API  | Anthopic   |
| SimpleAzureClient    | Azure部署的opeai GTP API     | openai     |
| DeepSeekClient       | DeepSeek                    | openai     |
| QianWenClient        | 同义千问                     | dashscope  |
| MoonShotClient       | MooonShot                   | openai     |
| GLMClient            | 智谱                        | zhipuai(需自行安装)    |
| ErnieApiClient       | 百度文心一言                 | 无依赖     |
| DoubaoApiClient      | 字节的火山引擎               | 火山 SDK(需自行安装)   |
| GeminiAPIClient      | Google的Gemini(国内无法访问) | google cloud(需自行安装) |
| BaichuanClient      | 百川                          | 无依赖      |
| HunyuanClient        | 腾讯混元 | 腾讯云hunyuan sdk (需自行安装) |
| MiniMaxClient        | 上海稀宇科技                   | 无依赖      |
| OpenAIClient         | OPENAI                        | openai    |
| Zero1LLamaImproverClient| 零一                        | openai    |

__陆续还在添加其他LLM API的支持，有需要可以pr 或者 issue__


## 如何填写
- **llm_api**  可选值,除了填写 api_key, 还需要安装依赖项 , 申请 api_key 的时候，应该都知道安装什么依赖项
    * **SimpleClaudeAwsClient**:  Aws的 Claude API ，国内可用，依赖 Anthopic 库，这是目前开发和测试用的API
    * **SimpleAzureClient**:  Azure的 OpenAI API，国内可用，依赖 openai 库
    * **DeepSeekClient**:  DeepSeek的 API (依赖openai库)
    * **QianWenClient**: 同义千问的 API (还没测试,依赖dashscope库)
    * **MoonShotClient**: MooonShot的 API (还没测试,依赖openai库)
    * **GLMClient**: 智谱的GLM API (还没测试,依赖 zhipuai库)
    * **ErnieApiClient**: 百度文心一言的 API (还没测试，无依赖)
    * **DoubaoApiClient**: 字节的火山引擎 豆包 API (还没测试，依赖火山 SDK)
    * **GeminiAPIClient**: Google 的 Gemini API (国内不可用，依赖 google cloud 库)
    * **BaichuanClient**: 百川的 API (还没测试，无依赖)
    * **HunyuanClient**: 腾讯混元 API (还没测试，依赖 tencentcloud-sdk-python-hunyuan 库)
    * **MiniMaxClient**: 上海稀宇科技的 API (还没测试，无依赖)
    * **OpenAIClient**: OPENAI API (众所周知，国内不可用，依赖openai库)
    * **Zero1LLamaImproverClient**: 零一 API (还没测试，依赖openai库)
- llm_cheap_api 建议使用CheapMiniMax(目前赠送1亿tokens) ,需要配置对应API KEY
- embedding_api 文本向量化用，如果你注册了MiniMax，那个建议使用MiniMax的embedding
- ranker_api 用于二次排序，暂时不用填
- talker = CliTalker  要用cli模式,就不要动这个 
- 后面的 api_key , 不同都填，选择哪个 LLM API，就填哪个 api_key
- tushare_key 如果要使用tushare,必须配置有效key，如果不配置key，tushare是不会启用的

## 运行
```bash
# 启动cli
python cli.py

# 启动web
python main.py
```

## 特殊指令
- 第一个 query 不接受指令，必须输入一个数据查询之后，才能输入指令。比如：分析今年上证指数走势
- help 显示帮助信息
- clear_history 清除历史记录，当前版本需要手动刷新一下
- export 导出代码
- go 执行计划
- modify_step_code=step_number query 修改指定步骤的代码
- redo 重新执行(不会生成代码)
- 除此之外的指令还不完善，暂时别用

## 如何使用
### 1. 输入一个查询
```text
分析今年上证指数走势
```
你会获得一个执行计划，如下：
```js
{
  query_summary: '分析今年上证指数走势',
  steps: [
    {
      step_number: 1,
      description: '获取今年上证指数的历史数据',
      type: 'data_retrieval',
      data_category: '指数数据',
      save_data_to: 'shanghai_index_data'
    },
    {
      step_number: 2,
      description: '获取相关的宏观经济数据',
      type: 'data_retrieval',
      data_category: '宏观经济数据',
      save_data_to: 'macro_economic_data'
    },
    {
      step_number: 3,
      description: '分析上证指数走势，重点关注：\n1. 整体趋势\n2. 关键转折点\n3. 成交量变化\n4. 与宏观经济数据的关联',
      type: 'data_analysis',
      required_data: [
        'shanghai_index_data',
        'macro_economic_data'
      ]
    },
    {
      step_number: 4,
      description: '总结分析结果，提供今年上证指数走势的综合报告',
      type: 'data_analysis',
      required_data: [
        'shanghai_index_data',
        'macro_economic_data'
      ]
    }
  ]
}
```

### 2. 删除/增加步骤
```text
删除步骤 3
```

### 3. 修改计划细节
```text
修改步骤 3：从成交量，关键支撑和阻力，整体趋势，关键转折点，于宏观数据关联等方面进行分析
```

### 4. 检查计划
 反复修改，确认一个符合你心意的计划

### 5. 执行计划
```text
执行计划
```

## 安全及免责说明
- ⚠️代码中含有执行任意代码的功能，并且目前不在沙盒中运行。还拥有生成代码的的功能，理论上说，有可能生成对你的电脑产生危害。如果你不知道自己在做什么，请不要使用本项目。反之，使用本项目意味着你自担风险。
- ⚠️akshare 的 api 基本来自公开数据，可能有滞后性，甚至可能未必准确
- ⚠️LLM API 生成的报告未必准确，且未必专业，仅供参考，批判使用
- ⚠️作者只提供一个代码生成工具，不提供任何保证，也不提供投资建议和咨询。如果使用者依据数据和代码结果为依据进行投资，风险自负。

## 不足和缺陷
- 免费API和收费的相比，限制很多，不是所有功能都能实现。比如财联社电报，只能获取300条。如果想要更优质的数据，只能更换数据源。
- 绝大部分免费API实时性不高，不具备实时分析的条件，如果想要实时分析，可能只能自己购买付费数据源。
- LLM API的参数和提示词，都是需要经过慢慢调试的，必须在使用中不断调整，才能获得更好的效果。所以这个项目用的人越多，质量会越好。
- 目前很多LLM API没有被测试，理论可以运行，但是参数没被调教，LLM API也有自己的特性，所以LLM API的效果和结果可能存在非常大的差异。
- 分析思路和方法也是需要逐步积累的，目前积累尚浅，很多分析未必产生很好的效果，需要很详细的提示词，当然随着积累，能越来越好。
- 主体代码尚不完善，很多功能没有实现，需要慢慢完善。也请使用的朋友耐心，遇到问题积极反馈，我们一起来完善这个项目。
- 是不是只要把所有问题交给AI就行，自己可以躺平？不是的，AI的知识也是有限的，也需要你的经验和知识的辅助，这样能让AI更强大。

## 相关项目  
- [akshare](https://github.com/jindaxiang/akshare)  akshare数据源
- [tushare](https://tushare.pro/) tushare数据源
- [ak_code_library](https://github.com/wxy2ab/ak_code_library)  由akinterpreter 生成的代码，会放在这个仓库，方便大家使用
- [llm_dealer](https://github.com/wxy2ab/llm_dealer)  llm交易员，AI选股等实验性项目

## 关注公众号获得更多信息
![公众号](https://files.mdnice.com/user/71245/352a9efa-2033-4b15-9c47-006f78f20893.jpg)
