from core.llms.claude_aws_client import ClaudeAwsClient

def test1_claude_client():
    client = ClaudeAwsClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_gpt_client():
    from core.llms.azure_gpt_client import AzureGPT4oClient
    client = AzureGPT4oClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_deepseek_client():
    from core.llms.deep_seek_client import DeepSeekClient
    client = DeepSeekClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)
    
def test1_ernie_client():
    from core.llms.ernie_client import ErnieApiClient
    client = ErnieApiClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_moonshot_client():
    from core.llms.moonshot_client import MoonShotClient
    client = MoonShotClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_qianwen_client():
    from core.llms.qianwen_client import QianWenClient
    client = QianWenClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_glm_client():
    from core.llms.glm_client import GLMClient
    client = GLMClient()
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test1_llm_factory():
    from core.llms.llm_factory import LLMFactory
    factory = LLMFactory()
    print(factory.list_available_llms())
    client = factory.get_instance("")
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)

def test_data_interpreter():
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
    print("\n" + "="*50 + "\n")
    print("分析报告:")
    print(report)