---
title: 配置api_key
nextjs:
  metadata:
    title: 配置api_key
    description: 每个LLM API都必须配置自己的api_key.
---

大家选择自己的LLM API的时候，肯定就注册了对应的api_key. 使用前需要进行配置。

---

##  配置文件

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

## 配置方法

不是每个key都要填    
选择好自己的LLM API之后，在配置文件中填入对应的api_key

```ini
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



### Natus aspernatur iste



---

