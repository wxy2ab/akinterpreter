

from core.utils.single_ton import Singleton
from core.tushare_doc.ts_code_matcher import StringMatcher
import akshare as ak

class StockSymbolProvider(StringMatcher, metaclass=Singleton):
    def  __init__(self):
        spot =  ak.stock_zh_a_spot_em()
        index_cache="./json/stock_stock_zh_a_spot.pickle"
        super().__init__(spot, index_cache=index_cache, index_column='名称', result_column='代码')
    def __getitem__(self, query):
        return self.rapidfuzz_match(query)