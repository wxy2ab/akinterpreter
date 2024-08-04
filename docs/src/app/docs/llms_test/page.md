---
title: LLM推荐排序
nextjs:
  metadata:
    title: LLM推荐排序
    description: 经过不太严谨的测试，这是目前的排名
---

LLM API在 akinterpreter表现是不一样的，下面是经过一些不太严谨的测试之后获得的一个排序。当然，LLM API虽然都在更新。具体使用体验还是要自己尝试。我也会不定期更新。
---

## LLM测试排序


| 推荐排名 | 客户端名称               | 推荐理由                                                                 |
| -------- | -------------------------- | ---------------------------------------------------------------------- |
| 1        | SimpleClaudeAwsClient      | 国内可用，质量最高，速度最快，价格不算贵                                                     |
| 2        | SimpleDeepSeekClient       | 价格非常便宜，注册容易                                                               |
| 3        | SimpleAzureClient         | 国内可用，质量不错，但价格较高（Azure 上还没有 GPT-4o-mini）                                  |
| 4        | MiniMaxClient             | 质量不错，速度很快                                                                 |
| 5        | GLMClient                | 质量不错，但速度有点慢                                                               |
| 6        | ErnieApiClient            | 代码质量不太高                                                                   |
| 7        | HunyuanClient             | 速度有点慢                                                                    |
| 8        | QianWenClient             | 速度比较慢，生成质量也一般                                                               |
| 9        | Zero1LLamaImproverClient | 速度很慢，质量很一般                                                               |
| 10       | MoonShotClient           | 内容审查过于严格，很正常的新闻内容会报内容不适的错误                                                     |
| 11       | SimpleDoubaoClient        | 其实价格很便宜，就是速度太慢，如果速度改善可能和不错                                                   |
| 12       | BaichuanClient            | 指令响应很差                                                                   |
| 13       | SparkClient               | API 会莫名其妙报500错误，查不到error_code                                                       |
| 14       | ClaudeClient              | 国内无法访问                                                                   |
| 15       | OpenAIClient              | 国内无法访问                                                                   |
| 16       | GeminiAPIClient           | 国内无法访问                                                                   |


## 关于SimpleClaudeAwsClient
Claude API各方面的使用体验都是非常不错的。 生成速度也非常优秀。 而且国内可以访问。 唯一的缺陷就是注册需要一些技巧。   
如果不知道怎么注册的家人们可以联系我(github页面底部有微信)，我可以教大家。如果想知道的人多，我考虑把过程写出来。   

## 关于SimpleDeepSeekClient
DeepSeek API的速度还不错，质量只能说不算差，但是真便宜。 价格非常便宜，注册也很简单，确实是比较推荐了，我也会针对DeepSeek做一些优化。   

## 关于SimpleAzureClient
最大的遗憾就是Azure上还不支持GPT-4o-mini , 这个国内可用的gpt4o 也是非常不错的，非常推荐。

## 关于MiniMaxClient
MiniMaxClient 从2024年8月1日起 1块钱100万tokens, 还送1亿tokens 那就非常舒适了， 可惜目前这个API版本MiniMax很难生成能执行的代码，代码方面比较薄弱，目前无法当作主力LLM。

## 其他
* 文心一言以后的API基本上因为各种各样的问题，可用性就不太好了，当然我以后也会加入更多API的支持。但是目前可用性尚可的就是文心一言前面的几个API。
* 每个API适合做不同类型任务的参数其实是不一样的，现在分的还不是很细，参数优化也还没做。可能针对任务调整参数之后结果会变得不一样。
* 这个排名很粗糙，所以也许是有偶然性的，随着时间的推进，测试增多，排名也会有所调整。
