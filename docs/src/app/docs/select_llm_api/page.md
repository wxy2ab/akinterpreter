---
title: 配置llm_api
nextjs:
  metadata:
    title: 配置llm_api
    description: 配置llm_api就是选择AI.
---

akinterpreter 提供了多种LLM API的支持，选择你喜欢的API，配置好对应的api_key，就可以使用了

---

##  支持的llm_api 列表

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


## 如何填写

把setting.ini.template复制一份，然后更名为setting.ini    
你会看到开头是这样的
```ini
[Default]
llm_api = SimpleDeepSeekClient
llm_cheap_api = CheapMiniMax
embedding_api = MiniMaxEmbedding
ranker_api = BaiduBCEReranker
talker = CliTalker
```
你需要配置的就是 llm_api 对面内容   
llm_api 必须是`支持的llm_api 列表`里面的`类名`   
比如，如果你想选择DeepSeek,就应该输入 llm_api = SimpleDeepSeekClient    

## 推荐配置1
推荐大家选择SimpleClaudeAwsClient,因为这个是开发用的   
而且就目前而言，就写代码这个任务来说，Claude的产出能力还是显著高于其他的   
所有有条件的，建议使用
但是注意，你要去申请aws bedrock 的api   
Google和anhtopic的api国内都是用不了的     

## 推荐配置2
SimpleDeepSeekClient   
DeepSeek的API注册简单，费用也很低，非常推荐   
DeepSeek 目前价格确实很有竞争力   
而且有128k的上下文，最高8k的输出     
就价格而言，豆包的价格也很低   
但是真心不建议普通人去折腾火山引擎    
还有配置子账号什么的，我觉得对普通人太不友好了    
注册简单，配置简单，价格便宜的，就是SimpleDeepSeekClient   

## 其他LLM API
目前其他很多API都还没测试过    
只是调通了接口，理论上可以运行   
如果大家遇到任何问题，可以反馈   

## llm_cheap_api
国产LLM API目前还是很给力的。    
MiniMax的API 目前送一亿tokens 非常爽了  
不过这个API不适合生成代码，但是可以执行其他的文本任务   

## embedding_api
embedding_api 也也建议使用MiniMax的API   
封装的类是 MiniMaxEmbedding   
比较下来我还是推荐使用API ，而不是使用本地的embedding模型    
本地的embedding模型，都需要从huggingface 下载，需要点魔法🧙‍♀️才能实现    
另外本地的embedding模型，文件都是很大，基本1G以上，下载也需要时间    
如果没有GPU的话，好几个本地模型执行速度也很慢    
综合考虑，我还是建议使用API，避免麻烦    