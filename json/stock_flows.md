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
   - 使用 get_baidu_hotrank 获取百度热门股票列表,获取前50支热门股票
   - 使用 stock_market_desc 获取市场整体描述
   - 使用 get_market_news_300 获取市场新闻，然后用 summarizer_news 提取关键信息
   - 使用 summarize_historical_index_data 获取上证指数的近期走势
   输出:
   - hot_stocks: List[str] 热门股票代码列表
   - market_overview: str 市场整体描述
   - market_news_summary: str 市场新闻摘要
   - index_trend: str 上证指数近期走势

2. 分析所有选出股票
   输入: hot_stocks
   对每只热门股票进行以下分析：
   - 使用 get_stock_info 和 get_stock_a_indicators 获取股票详细信息
   - 使用 summarize_historical_data 获取股票近期历史数据
   - 使用 get_baidu_analysis_summary 获取百度分析摘要
   输出:
   - stock_analysis: Dict[str, Dict] 股票分析结果字典，结构如下：
     {
       "stock_code": {
         "name": str,
         "info": str,  # 股票详细信息
         "indicators": str,  # 股票指标
         "history": str,  # 历史数据摘要
         "baidu_analysis": str,  # 百度分析摘要
       },
       ...
     }

3. 短线潜力评估
   输入: stock_analysis, market_overview, market_news_summary, index_trend
   对每只热门股票进行LLM分析：
   - 生成评估提示词，包含：
     - 股票信息（从stock_analysis[stock_code]中获取）
     - 市场信息（使用market_overview, market_news_summary, index_trend）
     - 短线投资特定要求，明确指出：
       *  评估股票对市场情绪的敏感度（高/中/低）
       *  股票与当前热点事件的相关性（强/中/弱）
       *  股票的短期技术面走势（上升/震荡/下降）
       *  股票的流动性（以换手率为参考）
     - 要求返回JSON格式，包含：
       - "code": 股票代码
       - "name": 股票名称
       - "score": 短线潜力评分（0-100的整数），表示其和当前市场热点，情绪热点，短线潜力的匹配程度
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
   注意：

   确保使用正确的变量名访问股票信息：stock_analysis[stock_code]
   确保 attention 是数值类型
   在生成评估提示词时，明确指出短线投资的具体评估标准，明确要求明确返回结构
   为评分提供明确的解释和范围，使其与短线投资需求紧密相关
   使用code_tools.add("stock_evaluations", stock_evaluations)存储输出结果

4. 筛选和排序
   输入: stock_evaluations
   - 根据短线潜力评分、成交量、市场关注度等因素对股票进行综合排序
   - 创建一个包含所有必要信息的字典列表，每个字典包含：
     - "code": 股票代码
     - "name": 股票名称
     - "score": 短线潜力评分
     - "reason": 50个字以内的评分理由
     - "risks": 风险因素列表
     - "attention": 市场关注度
     - "turnover_rate": 换手率（如果可用）
   - 根据综合因素对这个列表进行排序，排序规则如下：
      1. 主要依据：短线潜力评分（score）
      2. 次要依据：市场关注度（attention）
      3. 辅助参考：换手率（turnover_rate，如果可用）
   - 如果换手率数据不可用，则仅使用短线潜力评分和市场关注度进行排序
   - 使用加权平均的方式计算综合得分，建议权重为：
      1. 短线潜力评分：70%
      2. 市场关注度：30%   ，注意，市场关注度和短线潜力评分不在同一个数值区间，不可直接乘以30%然后相加
   - 如果换手率数据可用，可以将其作为额外的参考因素，但不应过度影响排序
   - 选择排名靠前的股票（如前5只）作为推荐
   - 输出:
      recommended_stocks: List[Dict] 推荐股票列表，每个字典包含以下键：
      - "code", "name", "score", "reason", "risks", "attention", "turnover_rate"（如果可用）, "composite_score"（综合得分）
   - 注意：attention 来自LLM的输出,可能部分attention并非数值类型，需要去掉里面的描述性文字才能获得attention 的值

5. 生成推荐列表和输出结果
   输入: recommended_stocks, market_overview, market_news_summary, index_trend
   - 使用输入数据生成结构化报告
   - 报告应包含：
     - 市场整体情况概述（包括热点行业和事件）
     - 推荐的股票列表，每只股票包含：
       - 股票代码和名称
       - 短线潜力评分
       - 评分理由（50字以内）
       - 风险因素
       - 需关注的关键指标或事件（如成交量、市场关注度）
     - 整体风险提示
   输出:
   - output_result: str 最终的推荐报告

注意事项：
- LLM分析时，确保考虑短线投资特性，如对市场情绪、热点事件的敏感性
- 评估应特别注意股票的流动性、波动性和与市场热点的相关性
- 推荐应基于综合因素，包括技术面、消息面和资金面
- 清晰说明这只是基于当前数据的分析，不构成投资建议
- 强调短线投资的高风险性，建议用户进行进一步的研究和谨慎决策


### 快速股票推荐流程模板

1. 获取股票列表
   - 使用 "适合用于选择股票范围的函数" 获取一批股票
   - 如果用户没有指定范围，默认使用 get_baidu_hotrank 获取前30支热门股票
   输出:
   - stock_list: List[str] 股票代码列表

2. 快速收集关键信息
   输入: stock_list
   - 使用 stock_market_desc 获取市场整体描述
   - 使用 get_market_news_300 获取市场新闻，然后用 summarizer_news 提取关键信息
   - 对每只股票：
     - 使用 get_baidu_analysis_summary 获取百度分析摘要
     - 使用 summarize_historical_data 获取简要的历史数据摘要
   输出:
   - market_summary: str 市场整体描述
   - market_news_summary: str 市场新闻摘要
   - stock_info: Dict[str, Dict] 股票信息字典，结构如下：
     {
       "stock_code": {
         "baidu_analysis": str,  # 百度分析摘要
         "history": str,  # 历史数据摘要
       },
       ...
     }

3. 构建LLM分析提示词
   输入: stock_list, market_summary, market_news_summary, stock_info
   - 为每只股票创建一个简洁但信息丰富的提示词，包含：
     - 股票信息（从stock_info[stock_code]中获取）
     - 市场信息（使用market_summary, market_news_summary）
     - 投资特定要求，明确指出：
       * 评估股票对市场情绪的敏感度（高/中/低）
       * 股票与当前热点事件的相关性（强/中/弱）
       * 股票的短期技术面走势（上升/震荡/下降）
     - 要求返回JSON格式，包含：
       - "code": 股票代码
       - "name": 股票名称
       - "score": 潜力评分（0-100的整数），用于表示和筛选需求的匹配程度
       - "reason": 50字以内的评分理由
       - "risks": 列出主要风险点（字符串列表，最多3个）
       - "attention": 从评论摘要中提取的关注指数（如果可用，数值,确保是数值类型）
   输出:
   - prompts: Dict[str, str] 提示词字典，键为股票代码，值为对应的LLM分析提示词

4. LLM 分析步骤
   输入: prompts
   - 使用 llm_client.one_chat(prompt) 对每只股票进行分析
   - 解析LLM返回的JSON结果
   输出:
   - analysis_results: Dict[str, Dict] 分析结果字典，结构如下：
     {
       "stock_code": {
         "name": str,
         "score": int,
         "reason": str,
         "risks": List[str],
         "attention": float (如果可用)
       },
       ...
     }

5. 筛选和排序
   输入: analysis_results
   - 根据潜力评分和市场关注度对股票进行排序
   - 计算综合得分，建议权重为：
     1. 潜力评分：80%
     2. 市场关注度：20%（如果可用）
   - 选择排名靠前的股票（如前5只）作为推荐
   输出:
   - recommended_stocks: List[Dict] 推荐股票列表，每个字典包含以下键：
     "code", "name", "score", "reason", "risks", "attention"（如果可用）, "composite_score"

6. 生成推荐报告
   输入: recommended_stocks, market_summary, market_news_summary
   - 创建一个简洁的推荐报告，包含：
     - 市场整体情况概述（包括热点事件）
     - 推荐的股票列表，每只股票包含：
       - 股票代码和名称
       - 综合得分
       - 推荐理由（50字以内）
       - 主要风险因素（最多3个）
     - 整体风险提示
   输出:
   - output_result: str 最终的推荐报告

注意事项：
- 优化每个步骤的执行效率，保持整体流程的快速性
- 确保LLM提示词简洁明了，能快速提取和分析关键信息
- 强调分析基于有限信息，推荐仅供参考，不构成投资建议
- 清晰说明市场瞬息万变，推荐的时效性有限
- 建议用户在做出投资决策前进行更深入的研究
- 使用code_tools.add()存储每个步骤的关键输出
- 最后一步使用code_tools.add('output_result', final_report)存储最终报告

### 中长线股票推荐模板

1. 初始股票池筛选

- 使用 `get_institute_recommendations` 获取机构推荐股票，选择 "投资评级选股" 选项
- 使用 `get_top_holdings_by_market` 获取北向资金持仓前30只股票
- 合并去重，形成初始股票池

输出:
- `initial_stock_pool`: List[str] 初始股票代码列表

2. 市场概况分析

- 使用 `stock_market_desc` 获取市场整体描述
- 使用 `get_market_news_300` 获取市场新闻，用 `summarizer_news` 提取关键信息

输出:
- `market_overview`: str 市场整体描述
- `market_news_summary`: str 市场新闻摘要

3. 个股数据收集

对每只股票进行以下数据收集：
- 使用 `get_financial_analysis_summary` 获取财务分析摘要
- 使用 `get_stock_a_indicators` 获取股票市场指标
- 使用 `get_main_business_description` 获取主营业务描述
- 使用 `get_stock_profit_forecast` 获取盈利预测数据
- 使用 `get_baidu_analysis_summary` 获取百度分析摘要

输出:
- `stock_data`: Dict[str, Dict] 股票数据字典

4. LLM分析

输入: `stock_data`, `market_overview`, `market_news_summary`

对每只股票进行LLM分析：
- 生成评估提示词，包含收集的数据
- 使用 `llm_client.one_chat(prompt)` 进行评估
- 解析LLM返回的JSON结果

提示词模板：
作为一位经验丰富的金融分析师，请您基于以下信息对[股票代码]进行中长期投资价值分析：

市场概况：
[market_overview]
市场新闻摘要：
[market_news_summary]
公司基本信息：
[stock_data[stock_code]['business_description']]
财务分析摘要：
[stock_data[stock_code]['financial_summary']]
股票市场指标：
[stock_data[stock_code]['stock_a_indicators']]
盈利预测：
[stock_data[stock_code]['profit_forecast']]
百度分析摘要：
[stock_data[stock_code]['baidu_analysis']]

请提供以下分析，并以JSON格式返回：

growth_potential: 公司中长期成长潜力评估（1-100分）
financial_health: 财务健康状况评估（1-100分）
industry_outlook: 行业前景评估（1-100分）
competitive_advantage: 竞争优势分析（100字以内）
risk_factors: 潜在风险因素（列出top3）
investment_recommendation: 中长线投资推荐理由（200字以内）

在分析时，请特别注意以下几点：

公司的长期成长性和可持续发展能力
财务状况的稳定性和盈利能力的持续性
行业的长期发展趋势和公司在行业中的地位
公司的核心竞争力和创新能力
潜在的风险因素及其可能对公司长期发展的影响

请确保您的分析全面、客观，并提供有见地的洞察。您的评估将用于中长期投资决策，因此请着重考虑3-5年的发展前景。
请以JSON格式返回您的分析结果，包含上述6个字段。

输出:
- `stock_evaluations`: Dict[str, Dict] 股票评估结果字典，包含以下字段：
  - growth_potential: int (1-100)
  - financial_health: int (1-100)
  - industry_outlook: int (1-100)
  - competitive_advantage: str
  - risk_factors: List[str]
  - investment_recommendation: str

5. 筛选和排序

- 计算综合得分：
  综合得分 = 成长潜力 * 0.5 + 财务健康 * 0.3 + 行业前景 * 0.2
- 选择综合得分排名前10的股票

输出:
- `recommended_stocks`: List[Dict] 推荐股票列表

6. 生成推荐报告

输入: `recommended_stocks`, `market_overview`, `market_news_summary`

报告内容：
1. 市场概况
2. 推荐股票列表，每只股票包含：
   - 股票代码和名称
   - 综合得分
   - 成长潜力、财务健康、行业前景评分
   - 竞争优势
   - 主要风险
   - 投资建议
3. 风险提示

输出:
- `output_result`: str 最终的推荐报告

注意事项

- 关注公司长期成长性、财务稳健性和行业发展前景
- 考虑公司竞争优势和创新能力
- 基于综合因素提供推荐，包括基本面和行业趋势
- 清晰说明这是基于当前数据的分析，不构成投资建议
- 强调中长线投资需要持续关注公司发展和市场变化

### 个股行情解读模板

1) 数据收集

使用以下函数收集数据：

- `search_stock_code(stock_name)`: 获取股票代码
- `get_stock_info(stock_code)`: 获取股票基本信息
- `get_latest_stock_data(stock_code)`: 获取最新行情数据
- `get_historical_daily_data(stock_code, start_date, end_date)`: 获取最近30个交易日的历史数据
- `get_stock_a_indicators(stock_code)`: 获取A股个股指标
- `get_one_stock_news(stock_code, num=5)`: 获取最新的5条相关新闻
- `get_baidu_analysis_summary(stock_code)`: 获取百度分析摘要
- `get_stock_comments_summary()`: 获取该股票的千股千评数据
- `get_industry_pe_ratio("证监会行业分类", date)`: 获取行业市盈率数据
- `get_financial_analysis_summary(stock_code)`: 获取财务分析摘要
- `get_main_competitors(stock_code)`: 获取主要竞争对手信息
- `get_stock_profit_forecast(stock_code)`: 获取盈利预测数据

2) 数据分析

使用LLM分析收集到的数据，生成个股行情解读。提示词如下：

作为一位专业的股票分析师，请根据以下信息对 [股票代码] [股票名称] 的近期行情进行全面解读：

[插入所有收集到的数据]

请提供以下分析：

1. 股价走势分析（200字以内）：分析近期股价走势，包括关键支撑位和压力位，以及可能的突破点。
2. 成交量分析（150字以内）：解读成交量变化，评估买卖双方力量对比。
3. 基本面评估（250字以内）：
   - 基于公司财务数据，评估公司盈利能力、成长性和财务健康状况
   - 分析公司在行业中的竞争地位
   - 评估当前估值水平和增长潜力
4. 技术指标解读（200字以内）：解读主要技术指标（如MACD、KDJ、RSI等）的信号，预判可能的走势。
5. 消息面影响（150字以内）：分析近期新闻对股价的潜在影响。
6. 行业对比（200字以内）：
   - 将该股票与行业平均水平对比，评估其相对优势或劣势
   - 分析公司在行业中的市场份额和增长潜力
7. 风险分析（150字以内）：
   - 指出投资该股票可能面临的公司特有风险
   - 分析行业风险和宏观经济风险
8. 盈利预测与目标价（150字以内）：
   - 基于公司盈利预测，给出未来1-2年的业绩预期
   - 结合估值方法，提供合理目标价区间
9. 投资建议（200字以内）：
   - 基于以上分析，给出短期（1-2周）、中期（1-3个月）和长期（6-12个月）的投资建议
   - 提供具体的操作策略和注意事项

请确保您的分析客观、全面，并提供有见地的洞察。您的解读将帮助投资者理解该股票的近期表现并为投资决策提供参考。
请以JSON格式返回您的分析结果，包含上述9个字段。

3) 生成报告

基于LLM的分析结果，生成最终的个股行情解读报告。报告结构如下：

1. 股票概况
   - 基本信息
   - 最新行情数据
   - 公司简介

2. 走势分析
   - 近期股价走势
   - 成交量分析
   - 技术指标解读

3. 基本面评估
   - 财务状况分析
   - 盈利能力评估
   - 成长性分析
   - 行业地位评估

4. 估值分析
   - 当前估值水平
   - 与行业平均估值对比
   - 历史估值区间分析

5. 竞争力分析
   - 主要竞争对手对比
   - 市场份额分析
   - 核心竞争优势

6. 消息面分析
   - 近期相关新闻摘要
   - 消息对股价的潜在影响

7. 风险与机会
   - 公司特有风险因素
   - 行业风险
   - 宏观经济风险
   - 潜在投资机会

8. 盈利预测与目标价
   - 未来1-2年业绩预期
   - 目标价区间及依据

9. 投资建议
   - 短期操作建议
   - 中期投资策略
   - 长期投资观点
   - 风险控制建议



### 个股行情预测模板

1. 查询目的
为特定股票提供全面的行情预测，包括短期（1-5个交易日）、中期（1-3个月）和长期（6个月-1年）的价格走势、关键支撑位和压力位，以及潜在的投资机会和风险。

2. 数据收集

2.1 基础信息
- 股票选择：`search_stock_code(stock_name)` 获取股票代码 `stock_code`
- 基本信息：`get_stock_info(stock_code)`
- 主营业务：`get_main_business_description(stock_code)`
- A股指标：`get_stock_a_indicators(stock_code)`

2.2 行情数据
- 实时行情：`get_full_realtime_data()`
- 历史数据：`summarize_historical_data(stock_code, days=120)`

2.3 财务数据
- 财务分析：`get_financial_analysis_summary(stock_code)`
- 关键指标：`get_key_financial_indicators(stock_code)`

2.4 市场情绪和新闻
- 千股千评：`get_stock_comments_summary()[stock_code]`
- 相关新闻：`get_stock_news(stock_code, num=15)`
- 百度分析：`get_baidu_analysis_summary(stock_code)`
- 股票投票：`get_vote_baidu(stock_code)`

2.5 行业和市场数据
- 市场指标：`stock_market_desc()`
- 巴菲特指数：`get_current_buffett_index()`

2.6 机构观点
- 盈利预测：`get_stock_profit_forecast(stock_code)`
- 投资评级：`get_investment_ratings()`

2.7 额外数据（新增）
- 大股东变动：`get_shareholder_changes(stock_code)`
- 公司公告：`get_company_announcements(stock_code, num=5)`
- 行业对比：`get_industry_comparison(stock_code)`

3. 数据分析和处理步骤

3.1 数据预处理
a) 整合所有收集到的数据，形成综合数据集。
b) 进行数据异常检测，识别并处理异常值。
c) 对矛盾的数据进行标记和初步分析。

3.2 LLM分析
a) 使用LLM进行数据解读和初步分析报告生成。提示词如下：

作为一位资深的量化分析师和技术专家，请基于以下数据对 [股票代码] [股票名称] 未来的行情进行预测：

[插入整合后的数据集]

请提供以下分析：

1. 技术面分析（300字）：
   - 分析近期股价走势，识别关键支撑位和压力位
   - 评估成交量变化及其对价格的影响
   - 解读主要技术指标（如MACD、KDJ、RSI等）的信号
   - 基于技术分析，预测短期（1-5个交易日）、中期（1-3个月）和长期（6个月-1年）可能的价格区间

2. 基本面分析（300字）：
   - 评估公司近期财务表现和未来增长潜力
   - 分析行业地位和竞争优势
   - 对比行业平均水平，评估当前估值的合理性
   - 基于基本面分析，预测中长期走势

3. 市场情绪分析（200字）：
   - 解读千股千评数据和百度股市通投票数据
   - 分析近期新闻和公司公告对股价的潜在影响
   - 评估机构投资者的态度和预期

4. 宏观环境影响（200字）：
   - 分析当前市场整体环境（如巴菲特指数）对该股票的影响
   - 考虑可能影响该股票的宏观经济因素和行业政策

5. 风险因素（200字）：
   - 指出可能影响预测准确性的主要风险因素
   - 分析潜在的下行风险，包括公司特有风险和系统性风险
   - 评估监管政策变化的潜在影响

6. 投资建议（250字）：
   - 给出明确的短期、中期和长期投资建议
   - 提供具体的操作策略，包括建议的买入/卖出价位和止损位
   - 针对不同类型的投资者（如价值型、成长型）给出差异化建议

7. 预测置信度评估（150字）：
   - 对各个时间段的预测给出置信度评分（1-10分）
   - 解释影响置信度的主要因素

请确保您的分析全面、客观，并提供有理有据的预测。您的分析将用于指导投资决策，请保持专业和谨慎。
请以JSON格式返回您的分析结果，包含上述7个字段。

3.3 最终报告生成
使用LLM生成最终的个股行情预测报告。

4. 预期输出格式和内容

生成一份结构化的个股行情预测报告，包含以下部分：

1. 股票基本信息
   - 公司简介
   - 主营业务
   - 当前市场表现概览

2. 技术面分析
   - 近期走势分析
   - 关键支撑位和压力位
   - 技术指标解读
   - 短期、中期和长期价格区间预测

3. 基本面分析
   - 财务状况评估
   - 行业地位和竞争优势分析
   - 估值水平分析（包括与行业对比）
   - 中长期走势预测

4. 市场情绪和新闻分析
   - 投资者情绪解读
   - 近期重要新闻及公告分析

5. 宏观环境影响
   - 市场整体环境分析
   - 相关宏观经济因素讨论
   - 行业政策影响评估

6. 风险提示
   - 公司特有风险因素
   - 行业和市场系统性风险
   - 潜在监管风险

7. 投资建议
   - 短期操作策略
   - 中期投资建议
   - 长期投资展望
   - 针对不同类型投资者的建议

8. 预测置信度
   - 各时间段预测的置信度评分
   - 影响置信度的关键因素说明

9. 历史预测准确性回顾
   - 过去预测的准确率统计
   - 预测偏差分析和改进措施

10. 预测总结
    - 简明扼要的预测结论

5. 特殊考虑和注意事项

- 确保所有数据在生成报告前24小时内更新
- 对于小盘股、新上市公司或特殊行业股票，采用专门的分析流程
- 遇到重大突发事件时，启动紧急预测流程，增加人工分析比重
- 根据股票特性和市场环境，动态调整预测的时间范围
- 考虑全球经济趋势、汇率变化等跨市场因素对个股的潜在影响
- 在报告中明确指出预测的局限性和可能的误差范围
- 使用清晰、专业但易懂的语言，避免过于技术性的术语



### 股票组合分析与投资建议模板

1. 输入参数
- 股票列表：逗号分隔的股票代码或名称
- 资产总额：默认500万元
- 投资偏好：保本、保守、中性、进取、激进（默认中性）

2. 数据收集（针对每只股票）

2.1 股票基础数据
- 股票代码：`search_stock_code(stock_name)`
- 基本信息：`get_stock_info(stock_code)`
- A股指标：`get_stock_a_indicators(stock_code)`
- 实时行情：`get_realtime_stock_data(stock_code)`
- 历史数据摘要：`summarize_historical_data(stock_code, days=60)`

2.2 财务数据
- 财务分析摘要：`get_financial_analysis_summary(stock_code)`
- 财务预测：`get_financial_forecast_summary()[stock_code]`

2.3 市场情绪和分析
- 千股千评：`get_stock_comments_summary()[stock_code]`
- 百度分析：`get_baidu_analysis_summary(stock_code)`

2.4 行业数据
- 行业市盈率：`get_industry_pe_ratio(get_stock_sector(stock_code))`

2.5 机构观点
- 最新投资评级：`get_investment_ratings()`

2.6 市场整体数据
- 市场整体描述：`stock_market_desc()`

3. 数据分析和处理步骤

3.1 单只股票分析
对每只股票进行综合分析，使用以下LLM提示：

作为一位经验丰富的量化分析师，请基于以下数据对给定的股票进行分析并提供投资建议：

[插入单只股票的整合数据]

请提供以下分析，并以JSON格式返回结果：

{
  "stockCode": "股票代码",
  "stockName": "股票名称",
  "analysis": {
    "fundamental": "基本面分析（100字）",
    "technical": "技术面分析（100字）",
    "sentiment": "市场情绪分析（100字）"
  },
  "evaluation": {
    "strengths": ["优势1", "优势2", "优势3"],
    "weaknesses": ["劣势1", "劣势2", "劣势3"],
    "opportunities": ["机会1", "机会2", "机会3"],
    "threats": ["威胁1", "威胁2", "威胁3"]
  },
  "recommendation": {
    "shortTerm": {
      "outlook": "短期前景（看涨/看跌/持平）",
      "targetPrice": 数值,
      "action": "买入/增持/持有/减持/卖出"
    },
    "midTerm": {
      "outlook": "中期前景（看涨/看跌/持平）",
      "targetPrice": 数值,
      "action": "买入/增持/持有/减持/卖出"
    },
    "longTerm": {
      "outlook": "长期前景（看涨/看跌/持平）",
      "targetPrice": 数值,
      "action": "买入/增持/持有/减持/卖出"
    },
    "riskLevel": "低/中低/中/中高/高",
    "maxPositionPercentage": 数值（0-100）
  }
}

3.2 投资组合分析
基于单只股票的分析结果，进行整体投资组合分析。使用以下LLM提示：

作为一位投资组合经理，请基于以下单只股票的分析结果，对整个投资组合进行分析并提供建议。考虑总资产为[资产总额]元，投资偏好为[投资偏好]：

[插入所有股票的JSON分析结果]

请提供以下分析，并以JSON格式返回结果：

{
  "portfolioAnalysis": {
    "diversification": "组合多元化程度分析（100字）",
    "riskReturnProfile": "风险收益特征分析（100字）",
    "marketEnvironmentImpact": "当前市场环境对组合的影响分析（100字）"
  },
  "stockRecommendations": [
    {
      "stockCode": "股票代码",
      "stockName": "股票名称",
      "action": "买入/增持/持有/减持/卖出",
      "targetPosition": 数值（建议持仓金额），
      "positionPercentage": 数值（0-100，建议持仓比例）
    },
    // ... 重复上述结构for每只股票
  ],
  "riskManagement": {
    "majorRisks": ["主要风险1", "主要风险2", "主要风险3"],
    "riskManagementStrategies": ["风险管理策略1", "风险管理策略2", "风险管理策略3"]
  },
  "summary": "投资组合策略总结（200字）"
}

4. 输出格式

4.1 程序可读输出
直接输出3.2中生成的JSON结构。

4.2 人类可读报告
基于JSON结构生成一份结构化的报告，包含以下部分：

1. 投资组合概览
   - 分析的股票列表
   - 总资产和投资偏好
   - 组合的行业分布

2. 个股分析摘要
   - 每只股票的简要分析，包括基本面、技术面和市场情绪评估
   - 每只股票的SWOT分析

3. 组合整体分析
   - 多元化程度评估
   - 整体风险收益特征
   - 当前市场环境的影响分析

4. 投资建议
   - 每只股票的具体操作建议和目标持仓
   - 组合调整建议

5. 风险管理
   - 组合面临的主要风险因素
   - 风险管理策略建议

6. 总结
   - 投资组合策略概述

5. 特殊考虑和注意事项

- 确保所有数据在生成报告前12小时内更新
- 根据给定的投资偏好调整风险承受度和建议
- 考虑总资产规模，给出合理的持仓金额建议
- 考虑股票间的相关性，确保适度分散
- 特别关注组合中的异常表现者
- 考虑不同市值规模股票的特性
- 在报告中明确指出预测和建议的局限性
- 使用清晰、专业但易懂的语言