from core.llms.claude_aws_client import ClaudeAwsClient


def test1_claude_client():
    from core.utils.all_tools import tools_info_claude, AllTools
    client = ClaudeAwsClient()
    generator = client.tool_chat("写一个python函数，可以用于判断1000003是否是素数",
                                 tools_info_claude,
                                 AllTools,
                                 is_stream=True)
    for chunk in generator:
        print(chunk, end='', flush=True)

def test1_gpt_client():
    from core.llms.azure_gpt_client import AzureGPT4oClient
    client = AzureGPT4oClient()
    generator = client.text_chat("写一个python函数，可以用于判断1000003是否是素数",
                                 is_stream=True)
    for chunk in generator:
        print(chunk, end='', flush=True)

def test1_deepseek_client():
    from core.utils.all_tools import tools_info_gpt, AllTools
    from core.llms.deep_seek_client import DeepSeekClient
    client = DeepSeekClient()
    generator = client.tool_chat("写一个python函数，可以用于判断1000003是否是素数",
                                 tools=tools_info_gpt,
                                 function_module=AllTools,
                                 is_stream=True)
    for chunk in generator:
        print(chunk, end='', flush=True)

def test1_gemini_client():
    from core.utils.all_tools import get_gemini_tool_info, AllTools
    from core.llms.gemini_client import GeminiAPIClient
    tools_info = get_gemini_tool_info()
    client = GeminiAPIClient("wxy2ab")
    generator = client.tool_chat("写一个python函数，可以用于判断1000003是否是素数",
                                 tools_info,
                                 AllTools,
                                 is_stream=True)
    for chunk in generator:
        print(chunk, end='', flush=True)

def test1_ernie_client():
    from core.llms.ernie_client import ErnieApiClient
    from core.utils.all_tools import tools_info_gpt, AllTools
    client = ErnieApiClient()
    iterator = client.tool_chat("写一个python函数，可以用于判断1000003是否是素数,调用工具执行代码进行判断",
                                tools=tools_info_gpt,
                                function_module=AllTools,
                                is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_simple_claude():
    from core.llms._llm_api_client import LLMApiClient
    from core.llms.llm_factory import LLMFactory
    from core.utils.all_tools import tools_info_claude, AllTools
    factory= LLMFactory()
    client:LLMApiClient= factory.get_instance("SimpleClaudeAwsClient")
    iterator= client.tool_chat("北京的天气",
                               tools = tools_info_claude,
                                function_module=AllTools,
                               is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_simple_azure():
    from core.llms._llm_api_client import LLMApiClient
    from core.llms.llm_factory import LLMFactory
    from core.utils.all_tools import tools_info_gpt, AllTools
    factory= LLMFactory()
    client:LLMApiClient= factory.get_instance("SimpleAzureClient")
    iterator= client.tool_chat("写一个python函数，运行判断1000003是否是素数",
                               tools = tools_info_gpt,
                                function_module=AllTools,
                               is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_moonshot_client():
    from core.utils.all_tools import tools_info_gpt, AllTools
    from core.llms.moonshot_client import MoonShotClient
    client = MoonShotClient()
    iterator = client.tool_chat("现是几点",
                                tools=tools_info_gpt,
                                function_module=AllTools,
                                is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_qianwen_client():
    from core.llms.qianwen_client import QianWenClient
    from core.utils.all_tools import tools_info_gpt, AllTools
    client = QianWenClient()
    iterator = client.tool_chat("北京的天气",
                                tools=tools_info_gpt,function_module=AllTools,
                                is_stream=False)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_glm_client():
    from core.utils.all_tools import tools_info_gpt, AllTools
    from core.llms.glm_client import GLMClient
    client = GLMClient()
    result = client.tool_chat("现在几点了",
                              tools=tools_info_gpt,
                              function_module=AllTools,
                              is_stream=False)
    for chunk in result:
        print(chunk, end='', flush=True)

def test1_doubao_client():
    from core.llms.doubao_client import DoubaoApiClient
    from core.utils.all_tools import tools_info_gpt, AllTools
    client = DoubaoApiClient()
    iterator = client.tool_chat("北京的天气",
                                tools=tools_info_gpt,function_module=AllTools,
                                is_stream=False)
    print(iterator)

def test1_llm_factory():
    from core.llms._llm_api_client import LLMApiClient
    from core.llms.llm_factory import LLMFactory
    factory = LLMFactory()
    client: LLMApiClient = factory.get_instance()
    print(factory.list_available_llms())
    result = client.one_chat("我问你，你是不是豆包")  #("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_data_interpreter():
    import numpy as np
    import pandas as pd
    from core.interpreter.data_interpreter import DataInterpreter

    # 生成样本数据
    np.random.seed(42)  # 设置随机种子以确保结果可重现
    n = 100  # 样本数量

    # 生成相关的 A 和 B 数据
    A = np.random.randn(n)
    B = 2 * A + np.random.randn(n) * 0.5  # B 与 A 正相关，加入一些噪音

    # 创建 DataFrame
    data = pd.DataFrame({'A': A, 'B': B})

    # 初始化 DataInterpreter
    interpreter = DataInterpreter()

    # 定义用户请求
    user_request = "分析 A 和 B 这两列数据的相关性，并提供可视化。"

    # 使用 interpreter 进行分析
    code, report = interpreter.interpret(data, user_request)

    # 打印生成的代码和报告
    print("生成的代码:")
    print(code)
    print("\n" + "=" * 50 + "\n")
    print("分析报告:")
    print(report)

def test1_akshare_interpreter():
    from core.planner.akshare_planner import AkshareInterpreterPlanner
    planner = AkshareInterpreterPlanner()
    result = planner.plan_and_execute("分析今年上半年上证指数走势")
    print(result)

def test1_embeddings():
    from core.utils.tsdata import check_proxy_running
    check_proxy_running("172.22.32.1", 10809, "http")
    from core.embeddings._embedding import Embedding
    from core.embeddings.embedding_factory import EmbeddingFactory
    factory = EmbeddingFactory()
    print(factory.list_available_embeddings())
    embedding: Embedding = factory.get_instance()
    result = embedding.convert_to_embedding(
        ["中国是世界上汽车出口最大的国家", "嫦娥火箭刚刚完成了登月采集月壤并返回的任务"])
    print(result)

def test1_volcengine_embeddings():
    from core.embeddings._embedding import Embedding
    from core.embeddings.embedding_factory import EmbeddingFactory
    factory = EmbeddingFactory()
    print(factory.list_available_embeddings())
    embedding: Embedding = factory.get_instance("VolcengineEmbedding")
    result = embedding.convert_to_embedding(
        ["中国是世界上汽车出口最大的国家", "嫦娥火箭刚刚完成了登月采集月壤并返回的任务"])
    print(result)

def test1_cross_encoder():
    from core.utils.tsdata import check_proxy_running
    check_proxy_running("172.22.32.1", 10809, "http")
    from sentence_transformers import CrossEncoder
    model = CrossEncoder('maidalun1020/bce-reranker-base_v1', max_length=512)
    scores = model.predict([["我是中国人", "去湖南的旅客"], ["嫦娥六号", "乘波体弹道飞行器"]])
    print(scores)

def test1_ranker_factory():
    from core.utils.tsdata import check_proxy_running
    check_proxy_running("172.22.32.1", 10809, "http")
    from core.embeddings._ranker import Ranker
    from core.embeddings.ranker_factory import RankerFactory
    factory = RankerFactory()
    ranker: Ranker = factory.get_instance()
    print(factory.list_available_rankers())
    ranker = factory.get_instance("BCEBaseRanker")
    result = ranker.get_scores([["中国是世界上汽车出口最大的国家", "嫦娥火箭刚刚完成了登月采集月壤并返回的任务"]])
    print(result)

def test1_excel_interpreter():
    from core.interpreter.excel_interpreter import ExcelInterpreter
    interpreter = ExcelInterpreter()
    path = "./output/sources_count.xlsx"
    code, report = interpreter.interpret(
        path, "这个excel文件显示了，过去一段时间内，一天24个小时，每个小时不同数据源的新闻数量，帮我分析这个文件，提取有用的信息")
    print(report)

def test1_chat_pdf():
    from core.utils.tsdata import check_proxy_running
    check_proxy_running("172.22.32.1", 10809, "http")
    from core.rag.chat_pdf import ChatPDF
    chatpdf = ChatPDF()
    #chatpdf.add_corpus("README.md")
    response, reference_results = chatpdf.predict("文档主要内容是什么")
    print(response)

def test1_sse_data_interpreter():
    from core.interpreter.sse_data_interpreter import SSEDataInterpreter
    interpreter = SSEDataInterpreter()
    data = [3,4]
    user_request = "找出集合中的最大值"
    iterator = interpreter.interpret(data, user_request, is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_simple_claude_multi_chat():
    from core.llms._llm_api_client import LLMApiClient
    from core.llms.llm_factory import LLMFactory
    from core.utils.all_tools import tools_info_claude, AllTools
    factory= LLMFactory()
    client:LLMApiClient= factory.get_instance("SimpleClaudeAwsClient")
    iterator= client.text_chat("37是不是素数",is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)
    iterator= client.text_chat("我上一个问的是什么问题",is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_simple_azure_multi_chat():
    from core.llms._llm_api_client import LLMApiClient
    from core.llms.llm_factory import LLMFactory
    from core.utils.all_tools import tools_info_claude, AllTools
    factory= LLMFactory()
    client:LLMApiClient= factory.get_instance("SimpleAzureClient")
    iterator= client.text_chat("37是不是素数",is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)
    iterator= client.text_chat("我上一个问的是什么问题",is_stream=True)
    for chunk in iterator:
        print(chunk, end='', flush=True)

def test1_all_multi_chat():
    from core.utils.tsdata import check_proxy_running
    from core.llms._llm_api_client import LLMApiClient
    from core.llms.llm_factory import LLMFactory
    from core.utils.all_tools import tools_info_claude, AllTools
    #check_proxy_running("172.22.32.1",10809,"http")
    factory= LLMFactory()
    #"AzureGPT4oClient","ClaudeAwsClient","SimpleAzureClient","SimpleClaudeAwsClient","DeepSeekClient","DoubaoApiClient","ErnieApiClient","GeminiAPIClient","GLMClient","MoonShotClient","QianWenClient"
    llms = [""]
    for llm in llms:
        print(llm)
        print("\n","="*50)
        client:LLMApiClient= factory.get_instance(llm)
        iterator= client.text_chat("37是不是素数",is_stream=True)
        for chunk in iterator:
            print(chunk, end='', flush=True)
        
        print("\n","*"*50)

        iterator= client.text_chat("57是不是素数",is_stream=True)
        for chunk in iterator:
            print(chunk, end='', flush=True)
        print("\n","="*50)

def test1_sse_planner():
    from core.planner.akshare_sse_planner import AkshareSSEPlanner
    planner = AkshareSSEPlanner()
    query = "分析中国主要股指近一个月的走势，并与美国股市进行对比"
    for response in planner.plan_chat(query):
        print(response)

def test1_session_api():
    import unittest
    suite = unittest.defaultTestLoader.loadTestsFromName('test.testsessionapi.TestSessionAPI')
    runner = unittest.TextTestRunner()
    runner.run(suite)

