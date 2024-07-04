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

def test_llm_factory():
    from core.llms.llm_factory import LLMFactory
    factory = LLMFactory()
    print(factory.list_available_llms())
    client = factory.get_instance("")
    result = client.one_chat("写一个python函数，可以用于判断1000003是否是素数")
    print(result)