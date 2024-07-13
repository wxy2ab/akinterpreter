"""
这里存放的是各种类型的embedding

大概会分成两大类，一类是依赖于sentence_transformers的embedding
另外一类是基于API的

依赖于sentence_transformers的基本都是本地执行，不消耗token
但是配置比较麻烦，需要下载模型，最主要都是默认从huggingface下载的，这个，你懂的，需要懂科学的小伙伴才能愉快的玩耍
如果你懂科学
你可以在程序开通加两行代码
from core.utils.tsdata import check_proxy_running
check_proxy_running("38.38.4.38","8888","http")
这样你就能顺利玩耍本地embedding了
"""