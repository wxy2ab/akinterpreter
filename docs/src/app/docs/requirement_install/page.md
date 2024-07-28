---
title: 安装依赖
nextjs:
  metadata:
    title: 安装依赖
    description: 不同LLM的依赖.
---

不同LLM的依赖如何安装

---

## 豆包

```bash
pip install 'volcengine-python-sdk[ark]'
```
**注意**：   
windows 安装volcengine-python-sdk[ark]会报错，请使用    
```text
设置：\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem 路径下的变量 LongPathsEnabled为 1 
```
或者使用免SDK的封装 *SimpleDoubaoClient*    


## 混元
```bash
pip install tencentcloud-sdk-python-hunyuan
```

## openai(默认已经安装)
````bash
pip install openai
````

##  千问(默认已经安装)
```bash
pip install dashscope
```

## 智谱AI
```bash
pip install  zhiquai
```

## gemini
```bash
pip install google-cloud-aiplatform
```

## claude(默认已经安装)
```bash
pip install anthropic[bedrock] 
```


