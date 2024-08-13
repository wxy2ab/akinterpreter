### 全市场范围筛选股票
1. 数据获取
   - 使用 get_full_realtime_data 函数获取市场全部行情数据
   - 对获取的数据进行初步筛选，去除以 ST 和 *ST 开头的股票

2. 查询解析
   - 分析用户的查询要求
   - 确定筛选分类，如价值投资、价值低估、市场活跃、市场热点等

3. 市场信息收集
   - 使用 get_market_news_300 获取最近的市场新闻
   - 使用 stock_market_desc 获取市场整体描述
   - 使用 summarize_historical_index_data 获取指数历史行情（如上证指数）

4. 个股分析
   - 对筛选后的每只股票进行循环处理：
     a. 使用"获取个股信息的函数"获取详细信息（如 get_stock_info, get_stock_a_indicators 等）
     b. 使用 summarize_historical_data 查询该股票的历史行情
     c. 结合个股数据、市场数据和查询要求，生成用于 LLM 评分的提示词
     d. 使用 llm_client.one_chat 进行评分和归纳，要求返回 JSON 格式的结果
     e. 解析 LLM 返回的结果，提取关键信息

5. 结果处理
   - 收集所有股票的评分结果
   - 对评分结果按照不同类别进行排序
   - 对每个类别，选择排名靠前的股票（如前5名）

6. 输出结果
   - 为每个类别返回筛选出的股票信息，包括：
     - 股票代码
     - 股票名称
     - 分类得分
     - 得分理由

注意事项：
- 确保所有步骤都考虑到查询的具体要求
- 在生成评分提示词时，要充分利用收集到的个股和市场数据
- LLM 评分结果应该输出为josn格式。便于于解析和后续处理
- 最终输出应该清晰、结构化，便于用户理解和使用

这些提示添加到所有tip_help之中
- code_tools.add(name,value)不允许添加重复的内容，在所有步骤中不允许重复，不能在循环内层中使用code_tools.add
- 对每支股票读取数据，如果需要在后续步骤使用，把这些数据存储于字典Dict[str,Any], 同一种类型只使用一次code_tools.add

### 百度热门股票短线推荐模板

1. 获取热门股票和市场信息
   - 使用 get_baidu_hotrank 获取百度热门股票列表
   - 使用 stock_market_desc 获取市场整体描述
   - 使用 get_market_news_300 获取市场新闻，然后用 summarizer_news 提取关键信息
   - 使用 summarize_historical_index_data 获取上证指数的近期走势
   输出:
   - hot_stocks: List[str] 热门股票代码列表
   - market_overview: str 市场整体描述
   - market_news_summary: str 市场新闻摘要
   - index_trend: str 上证指数近期走势

2. 分析热门股票
   输入: hot_stocks
   对每只热门股票进行以下分析：
   - 使用 get_stock_info 和 get_stock_a_indicators 获取股票详细信息
   - 使用 summarize_historical_data 获取股票近期历史数据
   - 使用 get_baidu_analysis_summary 获取百度分析摘要
   - 使用 get_stock_comments_summary 获取股票评论摘要
   输出:
   - stock_analysis: Dict[str, Dict] 股票分析结果字典，结构如下：
     {
       "stock_code": {
         "name": str,
         "info": str,  # 股票详细信息
         "indicators": str,  # 股票指标
         "history": str,  # 历史数据摘要
         "baidu_analysis": str,  # 百度分析摘要
         "comments_summary": str  # 股票评论摘要
       },
       ...
     }

3. 短线潜力评估
   输入: stock_analysis, market_overview, market_news_summary, index_trend
   对每只热门股票进行LLM分析：
   - 生成评估提示词，包含：
     - 股票信息（从stock_analysis中获取）
     - 市场信息（使用market_overview, market_news_summary, index_trend）
     - 短线投资特定要求（如对市场情绪、热点事件的敏感性）
     - 要求返回JSON格式，包含：
       - "code": 股票代码
       - "name": 股票名称
       - "score": 0-100的整数评分
       - "reason": 50字以内的推荐理由
       - "risks": 列出关键风险点（字符串列表）
       - "volume": 从股票信息中提取的成交量（数值）
       - "attention": 从评论摘要中提取的关注指数（数值）
   - 使用 llm_client.one_chat(prompt) 进行评估
   - 解析LLM返回的JSON结果
   输出:
   - stock_evaluations: Dict[str, Dict] 股票评估结果字典，结构如下：
     {
       "stock_code": {
         "name": str,
         "score": int,
         "reason": str,
         "risks": List[str],
         "volume": float,
         "attention": float
       },
       ...
     }

4. 筛选和排序
   输入: stock_evaluations
   - 根据短线潜力评分、成交量、市场关注度等因素对股票进行综合排序
   - 创建一个包含所有必要信息的字典列表，每个字典包含：
     - "code": 股票代码
     - "name": 股票名称
     - "score": 短线潜力评分
     - "reason": 推荐理由
     - "risks": 风险因素列表
     - "volume": 成交量
     - "attention": 市场关注度
   - 根据综合因素对这个列表进行排序
   - 选择排名靠前的股票（如前5只）作为推荐
   输出:
   - recommended_stocks: List[Dict] 推荐股票列表

5. 生成推荐列表和输出结果
   输入: recommended_stocks, market_overview, market_news_summary, index_trend
   - 使用输入数据生成结构化报告
   - 报告应包含：
     - 市场整体情况概述（包括热点行业和事件）
     - 推荐的股票列表，每只股票包含：
       - 股票代码和名称
       - 短线潜力评分
       - 推荐理由（50字以内）
       - 风险因素
       - 需关注的关键指标或事件（如成交量、市场关注度）
     - 整体风险提示
   输出:
   - output_result: str 最终的推荐报告

注意事项：
- 确保每个步骤的输出变量名称一致，并使用code_tools.add()存储
- LLM分析时，确保考虑短线投资特性，如对市场情绪、热点事件的敏感性
- 评估应特别注意股票的流动性、波动性和与市场热点的相关性
- 推荐应基于综合因素，包括技术面、消息面和资金面
- 清晰说明这只是基于当前数据的分析，不构成投资建议
- 强调短线投资的高风险性，建议用户进行进一步的研究和谨慎决策


### 快速股票推荐流程模板

1. 获取热门股票列表
   - 输入：用户的股票范围查询条件
   - 使用 "适合用于选择股票范围的函数" 获取一批股票
   - 输出：
     - stock_list: List[str] 热门股票代码列表

2. 快速收集关键信息
   - 输入：stock_list
   - 使用 stock_market_desc 获取市场整体描述
   - 对每只热门股票：
     - 使用 get_baidu_analysis_summary 获取百度分析摘要
     - 使用 summarize_historical_data 获取简要的历史数据摘要
   - 输出：
     - market_summary: str 市场整体描述
     - stock_info: Dict[str, Dict] 股票信息字典，键为股票代码，值为包含百度分析和历史数据摘要的字典

3. 构建LLM分析提示词
   - 输入：stock_list, market_summary, stock_info, 用户查询条件
   - 为每只股票创建一个简洁但信息丰富的提示词
   - 输出：
     - prompts: Dict[str, str] 提示词字典，键为股票代码，值为对应的LLM分析提示词

4. LLM 分析步骤
   - 输入：prompts
   - 对每只股票进行LLM分析
   - 输出：
     - analysis_results: Dict[str, Dict] 分析结果字典，键为股票代码，值为包含以下字段的字典：
       - score: int 0-100的评分
       - reason: str 不超过50字的推荐理由
       - risks: List[str] 关键风险因素列表

5. 生成推荐报告
   - 输入：market_summary, analysis_results
   - 创建一个简洁的推荐报告
   - 输出：
     - output_result: str 最终的推荐报告，包含：
       - 市场概况
       - 推荐股票列表（包括股票代码、名称、评分、推荐理由、风险提示）
       - 整体风险提醒

注意事项：
- 优化LLM提示词，确保能快速提取和分析关键信息
- 限制每只股票的分析时间，保持整体流程的快速性
- 强调LLM分析基于有限信息，推荐仅供参考
- 建议用户在做出投资决策前进行更深入的研究
- 清晰说明市场瞬息万变，推荐的时效性有限
- 确保每个步骤的输出变量与下一步骤的输入变量名称一致
- 在每个步骤中，使用code_tools.add()存储必要的中间结果
- 最后一步使用code_tools.add('output_result', final_report)存储最终报告
