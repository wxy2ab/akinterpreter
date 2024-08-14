import logging
import re
from typing import Any, Callable, List, Dict, Tuple, Optional, Union ,Literal
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import json
import akshare as ak
from core.llms._llm_api_client import LLMApiClient
from core.interpreter.data_summarizer import DataSummarizer
from core.interpreter.ast_code_runner import ASTCodeRunner
from .baidu_news import BaiduFinanceAPI
from .index_finder import index_finder
from .stock_symbol_provider import StockSymbolProvider
import ta



class StockDataProvider:
    def __init__(self,llm_client:LLMApiClient):
        self.llm_client = llm_client
        self.data_summarizer = DataSummarizer()
        self.code_runner = ASTCodeRunner()
        self.baidu_news_api = BaiduFinanceAPI()
        self.index_finder = index_finder
        self.stock_finder = StockSymbolProvider()
        
        self.code_name_list = {}
        self.previous_trading_date_cache = None
        self.previous_trading_date_cache_time = None
        self.latest_trading_date_cache = None
        self.latest_trading_date_cache_time = None
        self.cash_flow_cache = {}
        self.profit_cache = {}
        self.balance_sheet_cache = {}
        self.forecast_cache = {}
        self.report_cache = {}
        self.comment_cache = {}
        self.historical_data_cache = {}
        self.rebound_stock_pool_cache = {}  
        self.new_stock_pool_cache = {} 
        self.strong_stock_pool_cache = {}  
        self.previous_day_stock_pool_cache = {}

    def search_index_code(self,name:str)->str:
        """
        通过名称模糊查询指数代码。参数name:str,返回值str
        参数：
            name:str  用于搜索的名字
        返回值
            指数代码
        """
        return self.index_finder[name]

    def search_stock_code(self,name:str)->str:
        """
        通过名称模糊查询股票代码.参数name:str 返回值str
        参数
            name:str    用于搜索的名字
        返回值
            股票代码
        """
        return self.stock_finder[name]
    
    def _fetch_trading_dates(self):
        # 获取当前时间
        now = datetime.now()

        # 定义今天的日期
        today_str = now.strftime("%Y%m%d")
        start_date_str = (now - timedelta(days=10)).strftime("%Y%m%d")

        # 获取最近10天的交易数据，假设使用上证指数（000001.SH）
        stock_data = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date=start_date_str, end_date=today_str, adjust="")

        # 提取交易日期
        trading_dates = stock_data['日期'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d")).tolist()
        trading_dates.sort()
        return trading_dates

    def get_previous_trading_date(self) -> str:
        """
        获取最近一个交易日，不包含今天的日期,返回str 格式：YYYYMMDD
        """
        now = datetime.now()
        
        # 检查缓存是否有效
        if self.previous_trading_date_cache and self.previous_trading_date_cache_time.date() == now.date():
            return self.previous_trading_date_cache

        trading_dates = self._fetch_trading_dates()

        # 如果最近交易日期是今天，则返回上一个交易日期
        if trading_dates[-1].strftime("%Y%m%d") == now.strftime("%Y%m%d"):
            previous_trading_date = trading_dates[-2]
        else:
            previous_trading_date = trading_dates[-1]

        self.previous_trading_date_cache = previous_trading_date.strftime("%Y%m%d")
        self.previous_trading_date_cache_time = now
        return self.previous_trading_date_cache
    
    def get_latest_trading_date(self) -> str:
        """
        获取最近一个交易日。返回str 格式：YYYYMMDD
        如果当前时间是9:30之后，则，最近包含今天，否则不包含
        """
        now = datetime.now()
        cache_valid = False

        # 检查缓存是否有效
        if self.latest_trading_date_cache and self.latest_trading_date_cache_time.date() == now.date():
            if now.time() < datetime.strptime('09:30', '%H:%M').time():
                if self.latest_trading_date_cache_time.time() < datetime.strptime('09:30', '%H:%M').time():
                    cache_valid = True
            else:
                cache_valid = True

        if cache_valid:
            return self.latest_trading_date_cache

        trading_dates = self._fetch_trading_dates()
        include_today = now.time() >= datetime.strptime('09:30', '%H:%M').time()

        if include_today and trading_dates[-1].strftime("%Y%m%d") == now.strftime("%Y%m%d"):
            latest_trading_date = trading_dates[-1]
        else:
            latest_trading_date = trading_dates[-2] if trading_dates[-1].strftime("%Y%m%d") == now.strftime("%Y%m%d") else trading_dates[-1]

        self.latest_trading_date_cache = latest_trading_date.strftime("%Y%m%d")
        self.latest_trading_date_cache_time = now
        return self.latest_trading_date_cache

    def get_rebound_stock_pool(self, date: str = None) -> dict:
        """
        获取炸板股池数据并返回格式化结果。返回dict[symbol,str]
        
        参数:
            date (str): 交易日期，格式为 'yyyymmdd'。如果未提供，则获取最近一个交易日的数据。
        
        返回:
            dict: 键为股票代码，值为该股票的相关信息，格式化为易于读取的字符串。
        """
        if not date:
            date = self.get_previous_trading_date()
        
        # 检查缓存
        if date in self.rebound_stock_pool_cache:
            return self.rebound_stock_pool_cache[date]

        # 获取数据
        stock_pool_df = ak.stock_zt_pool_zbgc_em(date=date)

        # 处理数据
        result = {}
        for _, row in stock_pool_df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"最新价: {row['最新价']}, "
                f"涨停价: {row['涨停价']}, "
                f"成交额: {row['成交额']}元, "
                f"流通市值: {row['流通市值']}亿, "
                f"总市值: {row['总市值']}亿, "
                f"换手率: {row['换手率']}%, "
                f"涨速: {row['涨速']}, "
                f"首次封板时间: {row['首次封板时间']}, "
                f"炸板次数: {row['炸板次数']}, "
                f"涨停统计: {row['涨停统计']}, "
                f"振幅: {row['振幅']}, "
                f"所属行业: {row['所属行业']}"
            )
            result[row['代码']] = stock_info

        # 缓存结果
        self.rebound_stock_pool_cache[date] = result

        return result

    def get_new_stock_pool(self, date: str = None) -> dict:
        """
        获取次新股池数据并返回格式化结果。返回dict[symbol,str]
        
        参数:
            date (str): 交易日期，格式为 'yyyymmdd'。如果未提供，则获取最近一个交易日的数据。
        
        返回:
            dict: 键为股票代码，值为该股票的相关信息，格式化为易于读取的字符串。
        """
        if not date:
            date = self.get_previous_trading_date()
        
        # 检查缓存
        if date in self.new_stock_pool_cache:
            return self.new_stock_pool_cache[date]

        # 获取数据
        new_stock_pool_df = ak.stock_zt_pool_sub_new_em(date=date)

        # 处理数据
        result = {}
        for _, row in new_stock_pool_df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"最新价: {row['最新价']}, "
                f"涨停价: {row['涨停价']}, "
                f"成交额: {row['成交额']}元, "
                f"流通市值: {row['流通市值']}亿, "
                f"总市值: {row['总市值']}亿, "
                f"转手率: {row['转手率']}%, "
                f"开板几日: {row['开板几日']}, "
                f"开板日期: {row['开板日期']}, "
                f"上市日期: {row['上市日期']}, "
                f"是否新高: {row['是否新高']}, "
                f"涨停统计: {row['涨停统计']}, "
                f"所属行业: {row['所属行业']}"
            )
            result[row['代码']] = stock_info

        # 缓存结果
        self.new_stock_pool_cache[date] = result

        return result

    def get_strong_stock_pool(self, date: str = None) -> dict:
        """
        获取强势股池数据并返回格式化结果。返回dict[symbol,str]
        
        参数:
            date (str): 交易日期，格式为 'yyyymmdd'。如果未提供，则获取最近一个交易日的数据。
        
        返回:
            dict: 键为股票代码，值为该股票的相关信息，格式化为易于读取的字符串。
        """
        if not date:
            date = self.get_previous_trading_date()
        
        # 检查缓存
        if date in self.strong_stock_pool_cache:
            return self.strong_stock_pool_cache[date]

        # 获取数据
        strong_stock_pool_df = ak.stock_zt_pool_strong_em(date=date)

        # 处理数据
        result = {}
        for _, row in strong_stock_pool_df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"最新价: {row['最新价']}, "
                f"涨停价: {row['涨停价']}, "
                f"成交额: {row['成交额']}元, "
                f"流通市值: {row['流通市值']}亿, "
                f"总市值: {row['总市值']}亿, "
                f"换手率: {row['换手率']}%, "
                f"涨速: {row['涨速']}%, "
                f"是否新高: {row['是否新高']}, "
                f"量比: {row['量比']}, "
                f"涨停统计: {row['涨停统计']}, "
                f"入选理由: {row['入选理由']}, "
                f"所属行业: {row['所属行业']}"
            )
            result[row['代码']] = stock_info

        # 缓存结果
        self.strong_stock_pool_cache[date] = result

        return result

    def get_previous_day_stock_pool(self, date: str = None) -> dict:
        """
        获取昨日涨停股池数据并返回格式化结果。返回dict[symbol,str]
        
        参数:
            date (str): 交易日期，格式为 'yyyymmdd'。如果未提供，则获取最近一个交易日的数据。
        
        返回:
            dict: 键为股票代码，值为该股票的相关信息，格式化为易于读取的字符串。
        """
        if not date:
            date = self.get_previous_trading_date()
        
        # 检查缓存
        if date in self.previous_day_stock_pool_cache:
            return self.previous_day_stock_pool_cache[date]

        # 获取数据
        previous_day_stock_pool_df = ak.stock_zt_pool_previous_em(date)

        # 处理数据
        result = {}
        for _, row in previous_day_stock_pool_df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"最新价: {row['最新价']}, "
                f"涨停价: {row['涨停价']}, "
                f"成交额: {row['成交额']}元, "
                f"流通市值: {row['流通市值']}亿, "
                f"总市值: {row['总市值']}亿, "
                f"换手率: {row['换手率']}%, "
                f"涨速: {row['涨速']}%, "
                f"振幅: {row['振幅']}%, "
                f"昨日封板时间: {row['昨日封板时间']}, "
                f"昨日连板数: {row['昨日连板数']}, "
                f"涨停统计: {row['涨停统计']}, "
                f"所属行业: {row['所属行业']}"
            )
            result[row['代码']] = stock_info

        # 缓存结果
        self.previous_day_stock_pool_cache[date] = result

        return result

    def get_market_anomaly(self, indicator: Literal['火箭发射', '快速反弹', '大笔买入', '封涨停板', '打开跌停板', '有大买盘', '竞价上涨', '高开5日线', '向上缺口', '60日新高', '60日大幅上涨', '加速下跌', '高台跳水', '大笔卖出', '封跌停板', '打开涨停板', '有大卖盘', '竞价下跌', '低开5日线', '向下缺口', '60日新低', '60日大幅下跌'] = '大笔买入') -> dict:
        """
        获取指定类型的盘口异动信息，并返回格式化结果。indicator:str="大笔买入" 返回dict[symbol,str]
        
        参数:
            indicator (str): 盘口异动的类型，可以从以下选项中选择:
                - '火箭发射', '快速反弹', '大笔买入', '封涨停板', '打开跌停板', '有大买盘', 
                - '竞价上涨', '高开5日线', '向上缺口', '60日新高', '60日大幅上涨', 
                - '加速下跌', '高台跳水', '大笔卖出', '封跌停板', '打开涨停板', 
                - '有大卖盘', '竞价下跌', '低开5日线', '向下缺口', '60日新低', '60日大幅下跌'
        
        返回:
            dict: 键为股票代码，值为该股票的相关异动信息，格式化为易于读取的字符串。
        """
        # 获取数据
        market_anomaly_df = ak.stock_changes_em(symbol=indicator)

        # 处理数据
        result = {}
        for _, row in market_anomaly_df.iterrows():
            anomaly_info = (
                f"时间: {row['时间']}, "
                f"名称: {row['名称']}, "
                f"板块: {row['板块']}, "
                f"相关信息: {row['相关信息']}"
            )
            result[row['代码']] = anomaly_info

        return result

    def get_active_a_stock_stats(self, indicator: Literal['近一月', '近三月', '近六月', '近一年'] = "近一月") -> dict:
        """
        获取活跃 A 股统计数据，并返回格式化结果。参数indicator:str="近一月" 返回dict[symbol,str]
        
        参数:
            indicator (str): 统计时间范围，可以选择以下选项:
                - '近一月', '近三月', '近六月', '近一年'
        
        返回:
            dict: 键为股票代码，值为该股票的统计信息，格式化为易于读取的字符串。
        """
        # 获取数据
        active_stock_stats_df = ak.stock_dzjy_hygtj(symbol=indicator)

        # 处理数据
        result = {}
        for _, row in active_stock_stats_df.iterrows():
            stats_info = (
                f"证券简称: {row['证券简称']}, "
                f"最新价: {row['最新价']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"最近上榜日: {row['最近上榜日']}, "
                f"上榜次数-总计: {row['上榜次数-总计']}, "
                f"上榜次数-溢价: {row['上榜次数-溢价']}, "
                f"上榜次数-折价: {row['上榜次数-折价']}, "
                f"总成交额: {row['总成交额']}万元, "
                f"折溢率: {row['折溢率']}%, "
                f"成交总额/流通市值: {row['成交总额/流通市值']}%, "
                f"上榜日后平均涨跌幅-1日: {row['上榜日后平均涨跌幅-1日']}%, "
                f"上榜日后平均涨跌幅-5日: {row['上榜日后平均涨跌幅-5日']}%, "
                f"上榜日后平均涨跌幅-10日: {row['上榜日后平均涨跌幅-10日']}%, "
                f"上榜日后平均涨跌幅-20日: {row['上榜日后平均涨跌幅-20日']}%"
            )
            result[row['证券代码']] = stats_info

        return result

    def get_daily_lhb_details(self,date:str=None) -> dict:
        """
        获取龙虎榜每日详情数据，并返回格式化结果。返回dict[symbol,str]
        
        返回:
            dict: 键为股票代码，值为该股票的龙虎榜详情信息，格式化为易于读取的字符串。
        """
        if not date:
            date = self.get_latest_trading_date()
        
        # 获取数据
        lhb_details_df = ak.stock_lhb_detail_daily_sina(date=date)

        # 处理数据
        result = {}
        for _, row in lhb_details_df.iterrows():
            lhb_info = (
                f"股票名称: {row['股票名称']}, "
                f"收盘价: {row['收盘价']}元, "
                f"对应值: {row['对应值']}%, "
                f"成交量: {row['成交量']}万股, "
                f"成交额: {row['成交额']}万元, "
                f"指标: {row['指标']}"
            )
            result[row['股票代码']] = lhb_info

        return result

    def get_next_financial_report_date(self):
        """
        获取下一个财报发布日期(即将发生的). 返回值：str 格式：yyyymmdd

        """
        # 当前日期
        today = datetime.today()
        year = today.year
        month = today.month

        # 定义财报发行日期
        report_dates = [
            datetime(year, 3, 31),
            datetime(year, 6, 30),
            datetime(year, 9, 30),
            datetime(year, 12, 31)
        ]

        # 查找下一个财报发行日期
        for report_date in report_dates:
            if today < report_date:
                return report_date.strftime("%Y%m%d")

        # 如果当前日期在10月1日至12月31日之间，返回下一年的3月31日
        return datetime(year + 1, 3, 31).strftime("%Y%m%d")

    def get_latest_financial_report_date(self):
        """
        获取最近的财报发布日期(已经发生的)。 返回值：str 格式：yyyymmdd

        """
        # 当前日期
        today = datetime.today()
        year = today.year
        month = today.month

        # 定义财报发行日期
        report_dates = [
            datetime(year, 3, 31),
            datetime(year, 6, 30),
            datetime(year, 9, 30),
            datetime(year, 12, 31)
        ]

        # 查找最近的财报发行日期
        for report_date in reversed(report_dates):
            if today >= report_date:
                return report_date.strftime("%Y%m%d")

        # 如果当前日期在1月1日至3月30日之间，返回上一年的12月31日
        return datetime(year - 1, 12, 31).strftime("%Y%m%d")

    def stock_market_desc(self)->str:
        """
        获取市场总体描述信息，每个市场的市盈率，指数等信息。返回值str。
        """
        market_descriptions = []
        markets = ["上证", "深证", "创业板", "科创版"]
        for market in markets:
            try:
                df = ak.stock_market_pe_lg(symbol=market)
                if not df.empty:
                    latest_data = df.iloc[-1]
                    if market == "科创版":
                        description = f"{market}最新市值: {latest_data['总市值']:.2f}亿元，市盈率: {latest_data['市盈率']:.2f}"
                    else:
                        description = f"{market}最新指数: {latest_data['指数']:.2f}，平均市盈率: {latest_data['平均市盈率']:.2f}"
                    market_descriptions.append(description)
                else:
                    market_descriptions.append(f"{market}无数据")
            except Exception as e:
                market_descriptions.append(f"{market}数据获取失败: {e}")

        return "当前市场整体概况: " + "; ".join(market_descriptions)

    def get_a_stock_pb_stats(self) -> str:
        """
        获取A股等权重与中位数市净率数据。返回值str
        
        返回:
            str: A股市净率统计信息，包含日期、上证指数、市净率中位数、等权平均等信息。
        """
        # 获取数据
        pb_stats_df = ak.stock_a_all_pb()

        # 处理数据并生成易于理解的字符串
        result = []
        for _, row in pb_stats_df.iterrows():
            stats_info = (
                f"日期: {row['date']}, "
                f"全部A股市净率中位数: {row['middlePB']}, "
                f"全部A股市净率等权平均: {row['equalWeightAveragePB']}, "
                f"上证指数: {row['close']}, "
                f"当前市净率中位数在历史数据上的分位数: {row['quantileInAllHistoryMiddlePB']}, "
                f"当前市净率中位数在最近10年数据上的分位数: {row['quantileInRecent10YearsMiddlePB']}, "
                f"当前市净率等权平均在历史数据上的分位数: {row['quantileInAllHistoryEqualWeightAveragePB']}, "
                f"当前市净率等权平均在最近10年数据上的分位数: {row['quantileInRecent10YearsEqualWeightAveragePB']}"
            )
            result.append(stats_info)

        return "\n".join(result)

    def get_a_stock_pe_ratios(self) -> str:
        """
        获取A股等权重与中位数市盈率数据。返回值str
        
        返回:
            str: A股市盈率统计信息，包含日期、沪深300指数、市盈率中位数、等权平均等信息。
        """
        # 获取数据
        pe_ratios_df = ak.stock_a_ttm_lyr()

        # 处理数据并生成易于理解的字符串
        result = []
        for _, row in pe_ratios_df.iterrows():
            ratios_info = (
                f"日期: {row['date']}, "
                f"全A股滚动市盈率(TTM)中位数: {row['middlePETTM']}, "
                f"全A股滚动市盈率(TTM)等权平均: {row['averagePETTM']}, "
                f"全A股静态市盈率(LYR)中位数: {row['middlePELYR']}, "
                f"全A股静态市盈率(LYR)等权平均: {row['averagePELYR']}, "
                f"当前TTM(滚动市盈率)中位数在历史数据上的分位数: {row['quantileInAllHistoryMiddlePeTtm']}, "
                f"当前TTM(滚动市盈率)中位数在最近10年数据上的分位数: {row['quantileInRecent10YearsMiddlePeTtm']}, "
                f"当前TTM(滚动市盈率)等权平均在历史数据上的分位数: {row['quantileInAllHistoryAveragePeTtm']}, "
                f"当前TTM(滚动市盈率)等权平均在最近10年数据上的分位数: {row['quantileInRecent10YearsAveragePeTtm']}, "
                f"当前LYR(静态市盈率)中位数在历史数据上的分位数: {row['quantileInAllHistoryMiddlePeLyr']}, "
                f"当前LYR(静态市盈率)中位数在最近10年数据上的分位数: {row['quantileInRecent10YearsMiddlePeLyr']}, "
                f"当前LYR(静态市盈率)等权平均在历史数据上的分位数: {row['quantileInAllHistoryAveragePeLyr']}, "
                f"当前LYR(静态市盈率)等权平均在最近10年数据上的分位数: {row['quantileInRecent10YearsAveragePeLyr']}, "
                f"沪深300指数: {row['close']}"
            )
            result.append(ratios_info)

        return "\n".join(result)

    def get_current_buffett_index(self)->str:
        """
        获取当前巴菲特指数的最新数据.返回值str
        
        返回值:
            一个字符串，包含以下信息：
            - 收盘价
            - 总市值
            - GDP
            - 近十年分位数
            - 总历史分位数
        """
        # 获取数据
        data = ak.stock_buffett_index_lg()
        
        # 获取最后一行数据
        latest_data = data.iloc[-1]
        
        # 将最后一行数据转换为字符串
        buffett_index_info = (
            f"当前巴菲特指数: "
            f"收盘价: {latest_data['收盘价']}, "
            f"总市值: {latest_data['总市值']}, "
            f"GDP: {latest_data['GDP']}, "
            f"近十年分位数: {latest_data['近十年分位数']}, "
            f"总历史分位数: {latest_data['总历史分位数']}"
        )
        
        return buffett_index_info

    def get_stock_a_indicators(self, symbol: str) -> str:
        """
        获取指定股票的A股个股指标的最新数据.参数symbol:str 返回值str
        
        输入参数:
            symbol (str): 股票代码
            
        返回值 字符串类型:
            一个字符串，包含以下信息的描述：
            - 市盈率
            - 市盈率TTM
            - 市净率
            - 市销率
            - 市销率TTM
            - 股息率
            - 股息率TTM
            - 总市值
        """
        # 获取数据
        data = ak.stock_a_indicator_lg(symbol=symbol)
        
        # 获取最后一行数据
        latest_data = data.iloc[-1]
        
        # 将最后一行数据转换为字符串
        stock_indicators_info = (
            f"A股个股指标"
            f"股票代码: {symbol} 的最新A股个股指标: "
            f"市盈率: {latest_data['pe']}, "
            f"市盈率TTM: {latest_data['pe_ttm']}, "
            f"市净率: {latest_data['pb']}, "
            f"市销率: {latest_data['ps']}, "
            f"市销率TTM: {latest_data['ps_ttm']}, "
            f"股息率: {latest_data['dv_ratio']}, "
            f"股息率TTM: {latest_data['dv_ttm']}, "
            f"总市值: {latest_data['total_mv']}"
        )
        
        return stock_indicators_info

    def get_industry_pe_ratio(self, symbol: str, date: str = None) -> str:
        """
        获取指定日期和行业分类的行业市盈率数据。参数symbol:str 返回值str
        
        输入参数:
            symbol (str): 行业分类，选择 {"证监会行业分类", "国证行业分类"}
            date (str): 交易日，格式为 "YYYYMMDD"。如果未提供，则使用最近的一个交易日。
            
        返回值:
            一个字符串，包含以下信息的描述：
            - 行业分类
            - 行业层级
            - 行业编码
            - 行业名称
            - 公司数量
            - 纳入计算公司数量
            - 总市值-静态
            - 净利润-静态
            - 静态市盈率-加权平均
            - 静态市盈率-中位数
            - 静态市盈率-算术平均
        """
        if not date:
            date = self.get_previous_trading_date()
        
        # 获取数据
        data = ak.stock_industry_pe_ratio_cninfo(symbol=symbol, date=date)
        
        # 获取最后一行数据
        latest_data = data.iloc[-1]
        
        # 将最后一行数据转换为字符串
        industry_pe_ratio_info = (
            f"行业分类: {latest_data['行业分类']}, "
            f"行业层级: {latest_data['行业层级']}, "
            f"行业编码: {latest_data['行业编码']}, "
            f"行业名称: {latest_data['行业名称']}, "
            f"公司数量: {latest_data['公司数量']}, "
            f"纳入计算公司数量: {latest_data['纳入计算公司数量']}, "
            f"总市值-静态: {latest_data['总市值-静态']}亿元, "
            f"净利润-静态: {latest_data['净利润-静态']}亿元, "
            f"静态市盈率-加权平均: {latest_data['静态市盈率-加权平均']}, "
            f"静态市盈率-中位数: {latest_data['静态市盈率-中位数']}, "
            f"静态市盈率-算术平均: {latest_data['静态市盈率-算术平均']}"
        )
        
        return industry_pe_ratio_info

    def get_institute_recommendations(self, indicator: Literal['最新投资评级', '上调评级股票', '下调评级股票', '股票综合评级', '首次评级股票', '目标涨幅排名', '机构关注度', '行业关注度', '投资评级选股'] = "投资评级选股") -> dict:
        """
        获取机构推荐池数据，并返回格式化结果。 参数indicator:str="投资评级选股" 返回值Dict[symbol,str]
        
        参数:
            indicator (str): 选择的机构推荐类型，可以选择以下选项:
                - '最新投资评级', '上调评级股票', '下调评级股票', '股票综合评级', 
                - '首次评级股票', '目标涨幅排名', '机构关注度', '行业关注度', '投资评级选股'
        
        返回:
            dict: 键为股票代码，值为该股票的推荐信息，格式化为易于读取的字符串。
        """
        # 获取数据
        recommendations_df = ak.stock_institute_recommend(symbol=indicator)

        # 寻找股票代码列
        code_columns = ['股票代码', 'symbol', 'code']
        code_column = next((col for col in code_columns if col in recommendations_df.columns), None)

        if not code_column:
            raise ValueError("无法找到股票代码的列。")

        # 处理数据
        result = {}
        for _, row in recommendations_df.iterrows():
            recommendation_info = ", ".join([f"{col}: {row[col]}" for col in recommendations_df.columns if col != code_column])
            result[row[code_column]] = recommendation_info

        return result

    def get_recent_recommendations_summary(self, symbol: str) -> str:
        """
        获取指定股票的最近半年的评级记录统计.参数symbol:str 返回值str
        
        输入参数:
            symbol (str): 股票代码
            
        返回值:
            一个描述性的字符串，包含以下信息的统计：
            - 股票名称
            - 最近半年内的评级次数
            - 各种评级的次数统计（例如：买入、增持等）
            - 涉及的分析师数量
            - 涉及的评级机构数量
            - 目标价的最高值、最低值、平均值
            - 目标价的分布情况（最多的目标价区间）
        """
        # 获取数据
        data = ak.stock_institute_recommend_detail(symbol=symbol)
        
        # 计算最近半年的日期
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # 过滤最近半年的数据
        recent_data = data[data['评级日期'] >= six_months_ago.strftime('%Y-%m-%d')]
        
        # 统计股票名称
        stock_name = recent_data['股票名称'].iloc[0] if not recent_data.empty else "未知"
        
        # 统计评级次数
        total_recommendations = recent_data.shape[0]
        
        # 统计各种评级的次数
        rating_counts = recent_data['最新评级'].value_counts().to_dict()
        
        # 统计涉及的分析师数量
        analysts = recent_data['分析师'].str.split(',').explode().unique()
        num_analysts = len(analysts)
        
        # 统计涉及的评级机构数量
        institutions = recent_data['评级机构'].unique()
        num_institutions = len(institutions)
        
        # 统计目标价
        target_prices = recent_data['目标价'].replace('NaN', np.nan).dropna().astype(float)
        if not target_prices.empty:
            max_target_price = target_prices.max()
            min_target_price = target_prices.min()
            avg_target_price = target_prices.mean()
            
            # 计算目标价的分布情况
            bins = [0, 10, 20, 30, 40, 50, 100, 200, 300, 400, 500]
            target_price_distribution = np.histogram(target_prices, bins=bins)
            most_common_range_index = np.argmax(target_price_distribution[0])
            most_common_range = f"{bins[most_common_range_index]}-{bins[most_common_range_index + 1]}"
        else:
            max_target_price = min_target_price = avg_target_price = most_common_range = "无数据"
        
        # 生成描述性的字符串
        recommendation_summary = (
            f"股票代码: {symbol}, 股票名称: {stock_name}\n"
            f"最近半年内的评级次数: {total_recommendations}\n"
            f"评级统计:\n"
        )
        
        for rating, count in rating_counts.items():
            recommendation_summary += f" - {rating}: {count}次\n"
        
        recommendation_summary += (
            f"涉及的分析师数量: {num_analysts}\n"
            f"涉及的评级机构数量: {num_institutions}\n"
            f"目标价统计:\n"
            f" - 最高目标价: {max_target_price}\n"
            f" - 最低目标价: {min_target_price}\n"
            f" - 平均目标价: {avg_target_price:.2f}\n"
            f" - 最多的目标价区间: {most_common_range}\n"
        )
        
        return recommendation_summary

    def get_investment_ratings(self, date: str = None) -> dict:
        """
        获取投资评级数据，并返回格式化结果。返回值Dict[symbol,str]
        
        参数:
            date (str): 交易日期，格式为 'yyyymmdd'。如果未提供，则获取最近一个交易日的数据。
        
        返回:
            dict: 键为证券代码，值为该证券的投资评级信息，格式化为易于读取的字符串。
        """
        if not date:
            date = self.get_previous_trading_date()

        # 获取数据
        ratings_df = ak.stock_rank_forecast_cninfo(date=date)

        # 确定证券代码列
        code_columns = ['证券代码', 'symbol', 'code']
        code_column = next((col for col in code_columns if col in ratings_df.columns), None)

        if not code_column:
            raise ValueError("无法找到证券代码的列。")

        # 处理数据
        result = {}
        for _, row in ratings_df.iterrows():
            rating_info = ", ".join([f"{col}: {row[col]}" for col in ratings_df.columns if col != code_column])
            result[row[code_column]] = rating_info

        return result
    
    def get_financial_analysis_summary(self, symbol: str, start_year: str = "2024") -> str:
        """
        获取指定股票的财务分析指标，并返回易于理解的字符串形式的结果。参数symbol:str 返回值str

        参数:
            symbol (str): 股票代码。
            start_year (str): 查询的起始年份，默认为 "2024"。

        返回:
            str: 股票的最新财务分析指标，格式化为易于理解的字符串。
        """
        # 获取数据
        df = ak.stock_financial_analysis_indicator(symbol, start_year)
        
        # 取最后一行数据（最新数据）
        latest_data = df.tail(1).squeeze()

        # 生成易于理解的字符串
        result = "\n".join([f"{index}: {value}" for index, value in latest_data.items()])

        return result
 
    def get_key_financial_indicators(self, symbol: str, indicator: Literal["按报告期", "按年度", "按单季度"] = "按报告期") -> str:
        """
        获取指定股票的关键财务指标摘要，并返回易于理解的字符串形式的结果。参数symbol:str,indicator:str="按报告期" 返回值str

        参数:
            symbol (str): 股票代码。
            indicator (str): 财务指标的时间范围，可选值为 "按报告期", "按年度", "按单季度"。默认值为 "按报告期"。

        返回:
            str: 股票的关键财务指标摘要，格式化为易于理解的字符串。
        """
        # 获取数据
        df = ak.stock_financial_abstract_ths(symbol, indicator)

        # 取最新一行数据
        latest_data = df.tail(1).squeeze()

        # 生成易于理解的字符串
        result = "\n".join([f"{index}: {value}" for index, value in latest_data.items()])

        return result

    def get_stock_balance_sheet_by_report_em(self, symbol: str) -> str:
        """
        获取指定股票的最新资产负债表，并将所有列的数据拼接成一个字符串返回。参数symbol:str 返回值str

        参数:
        symbol (str): 股票代码。

        返回:
        str: 资产负债表的格式化字符串，包括所有319项数据。
        """
        df = ak.stock_balance_sheet_by_report_em(symbol)
        
        # 选择最新的一行数据
        latest_row = df.tail(1).iloc[0]
        
        # 将所有列的数据拼接成一个字符串
        balance_sheet_str = "\n".join([f"{col}: {latest_row[col]}" for col in df.columns])
        
        return balance_sheet_str

    def get_individual_stock_fund_flow_rank(self, indicator: str = "今日") -> dict:
        """
        获取个股资金流排名，并返回格式化结果。参数indicator:str="今日" 返回值Dict[symbol,str]

        参数:
            indicator (str): 资金流动的时间范围，可选值为 "今日", "3日", "5日", "10日"。默认值为 "今日"。

        返回:
            dict: 键为股票代码，值为该股票的资金流动信息，格式化为易于读取的字符串。
        """
        # 获取数据
        fund_flow_df = ak.stock_individual_fund_flow_rank(indicator=indicator)

        # 确定股票代码列
        code_columns = ['代码', 'symbol', 'code']
        code_column = next((col for col in code_columns if col in fund_flow_df.columns), None)

        if not code_column:
            raise ValueError("无法找到股票代码的列。")

        # 处理数据
        result = {}
        for _, row in fund_flow_df.iterrows():
            fund_flow_info = ", ".join([f"{col}: {row[col]}" for col in fund_flow_df.columns if col != code_column])
            result[row[code_column]] = fund_flow_info

        return result

    def get_individual_stock_fund_flow(self, symbol: str, market: str = "sh") -> dict:
        """
        获取指定股票的资金流动信息，并返回格式化结果。参数symbol:str market:str="sh" 返回值Dict[symbol,str]

        参数:
            symbol (str): 股票代码。
            market (str): 证券市场代码，可选值为 "sh"（上海证券交易所）、"sz"（深证证券交易所）、"bj"（北京证券交易所）。默认值为 "sh"。

        返回:
            dict: 键为股票代码，值为该股票的资金流动信息，格式化为易于读取的字符串。
        """
        # 获取数据
        fund_flow_df = ak.stock_individual_fund_flow(symbol=symbol, market=market)

        # 确定股票代码列
        code_columns = ['股票代码', 'symbol', 'code']
        code_column = next((col for col in code_columns if col in fund_flow_df.columns), None)

        if not code_column:
            raise ValueError("无法找到股票代码的列。")

        # 处理数据
        result = {}
        for _, row in fund_flow_df.iterrows():
            fund_flow_info = ", ".join([f"{col}: {row[col]}" for col in fund_flow_df.columns if col != code_column])
            result[row[code_column]] = fund_flow_info

        return result

    def get_cash_flow_statement_summary(self) -> dict:
        """
        获取最近一个财报发行日期的现金流量表数据摘要.返回值Dict[symbol,str]
        
        返回值:
            一个字典，键是股票代码，值是描述性的字符串，包含以下信息的统计：
            - 股票简称
            - 净现金流
            - 净现金流同比增长
            - 经营性现金流净额
            - 经营性现金流净额占比
            - 投资性现金流净额
            - 投资性现金流净额占比
            - 融资性现金流净额
            - 融资性现金流净额占比
            - 公告日期
        """
        # 获取最近的财报发行日期
        date = self.get_latest_financial_report_date()

        # 检查缓存是否存在
        if date in self.cash_flow_cache:
            return self.cash_flow_cache[date]
        
        # 获取数据
        data = ak.stock_xjll_em(date=date)
        
        # 生成描述性字符串的字典
        summary_dict = {}
        for index, row in data.iterrows():
            description = (
                f"股票简称: {row['股票简称']}, "
                f"净现金流: {row['净现金流-净现金流']}元, "
                f"净现金流同比增长: {row['净现金流-同比增长']}%, "
                f"经营性现金流净额: {row['经营性现金流-现金流量净额']}元, "
                f"经营性现金流净额占比: {row['经营性现金流-净现金流占比']}%, "
                f"投资性现金流净额: {row['投资性现金流-现金流量净额']}元, "
                f"投资性现金流净额占比: {row['投资性现金流-净现金流占比']}%, "
                f"融资性现金流净额: {row['融资性现金流-现金流量净额']}元, "
                f"融资性现金流净额占比: {row['融资性现金流-净现金流占比']}%, "
            )
            summary_dict[row['股票代码']] = description
        
        # 缓存结果
        self.cash_flow_cache[date] = summary_dict
        
        return summary_dict

    def get_profit_statement_summary(self) -> dict:
        """
        获取最近一个财报发行日期的利润表数据摘要.返回值Dict[symbol,str]
        
        返回值:
            一个字典，键是股票代码，值是描述性的字符串，包含以下信息的统计：
            - 股票简称
            - 净利润
            - 净利润同比
            - 营业总收入
            - 营业总收入同比
            - 营业总支出-营业支出
            - 营业总支出-销售费用
            - 营业总支出-管理费用
            - 营业总支出-财务费用
            - 营业总支出-营业总支出
            - 营业利润
            - 利润总额
            - 公告日期
        """
        date = self.get_latest_financial_report_date()

        # 检查缓存是否存在
        if date in self.profit_cache:
            return self.profit_cache[date]
        
        # 获取数据
        data = ak.stock_lrb_em(date=date)
        
        # 生成描述性字符串的字典
        summary_dict = {}
        for index, row in data.iterrows():
            description = (
                f"股票简称: {row['股票简称']}, "
                f"净利润: {row['净利润']}元, "
                f"净利润同比: {row['净利润同比']}%, "
                f"营业总收入: {row['营业总收入']}元, "
                f"营业总收入同比: {row['营业总收入同比']}%, "
                f"营业总支出-营业支出: {row['营业总支出-营业支出']}元, "
                f"营业总支出-销售费用: {row['营业总支出-销售费用']}元, "
                f"营业总支出-管理费用: {row['营业总支出-管理费用']}元, "
                f"营业总支出-财务费用: {row['营业总支出-财务费用']}元, "
                f"营业总支出-营业总支出: {row['营业总支出-营业总支出']}元, "
                f"营业利润: {row['营业利润']}元, "
                f"利润总额: {row['利润总额']}元, "
            )
            summary_dict[row['股票代码']] = description
        
        # 缓存结果
        self.profit_cache[date] = summary_dict
        
        return summary_dict

    def get_balance_sheet_summary(self) -> dict:
        """
        获取最近一个财报发行日期的资产负债表数据摘要.返回值Dict[symbol,str]
        
        返回值:
            一个字典，键是股票代码，值是描述性的字符串，包含以下信息的统计：
            - 股票简称
            - 资产-货币资金
            - 资产-应收账款
            - 资产-存货
            - 资产-总资产
            - 资产-总资产同比
            - 负债-应付账款
            - 负债-总负债
            - 负债-预收账款
            - 负债-总负债同比
            - 资产负债率
            - 股东权益合计
            - 公告日期
        """
        date = self.get_latest_financial_report_date()

        # 检查缓存是否存在
        if date in self.balance_sheet_cache:
            return self.balance_sheet_cache[date]
        
        # 获取数据
        data = ak.stock_zcfz_em(date=date)
        
        # 生成描述性字符串的字典
        summary_dict = {}
        for index, row in data.iterrows():
            description = (
                f"股票简称: {row['股票简称']}, "
                f"资产-货币资金: {row['资产-货币资金']}元, "
                f"资产-应收账款: {row['资产-应收账款']}元, "
                f"资产-存货: {row['资产-存货']}元, "
                f"资产-总资产: {row['资产-总资产']}元, "
                f"资产-总资产同比: {row['资产-总资产同比']}%, "
                f"负债-应付账款: {row['负债-应付账款']}元, "
                f"负债-总负债: {row['负债-总负债']}元, "
                f"负债-预收账款: {row['负债-预收账款']}元, "
                f"负债-总负债同比: {row['负债-总负债同比']}%, "
                f"资产负债率: {row['资产负债率']}%, "
                f"股东权益合计: {row['股东权益合计']}元, "
                f"公告日期: {row['公告日期']}"
            )
            summary_dict[row['股票代码']] = description
        
        # 缓存结果
        self.balance_sheet_cache[date] = summary_dict
        
        return summary_dict

    def get_stock_info(self,symbol:str)->pd.DataFrame:
        """
        公司概况
        输入参数:symbol	str	股票代码
        返回值:
            名称	类型	描述
            公司名称	object	-
            英文名称	object	-
            曾用简称	object	-
            A股代码	object	-
            A股简称	object	-
            B股代码	object	-
            B股简称	object	-
            H股代码	object	-
            H股简称	object	-
            入选指数	object	-
            所属市场	object	-
            所属行业	object	-
            法人代表	object	-
            注册资金	object	-
            成立日期	object	-
            上市日期	object	-
            官方网站	object	-
            电子邮箱	object	-
            联系电话	object	-
            传真	object	-
            注册地址	object	-
            办公地址	object	-
            邮政编码	object	-
            主营业务	object	-
            经营范围	object	-
            机构简介	object	-
        """
        return ak.stock_profile_cninfo(symbol=symbol)

    def get_stock_report(self, symbol: str) -> str:
        """
        获取指定股票的个股研报数据，过滤超过180天的数据，并进行统计分析（仅包含2024年数据）。返回值str

        参数:
            symbol (str): 股票代码。

        返回:
            str: 经过过滤和统计的个股研报数据，格式化为易于阅读的字符串。
        """
        # 获取数据
        reports_df = ak.stock_research_report_em(symbol)

        # 过滤超过180天的数据
        cutoff_date = datetime.now() - timedelta(days=180)
        reports_df['日期'] = pd.to_datetime(reports_df['日期'], errors='coerce')
        filtered_df = reports_df[reports_df['日期'] >= cutoff_date]

        if filtered_df.empty:
            return "没有找到最近180天内的研报数据。"

        # 统计分析，仅针对2024年数据
        stats = {
            "2024-盈利预测-收益": {
                "max": filtered_df["2024-盈利预测-收益"].max(),
                "min": filtered_df["2024-盈利预测-收益"].min(),
                "mean": filtered_df["2024-盈利预测-收益"].mean(),
            },
            "2024-盈利预测-市盈率": {
                "max": filtered_df["2024-盈利预测-市盈率"].max(),
                "min": filtered_df["2024-盈利预测-市盈率"].min(),
                "mean": filtered_df["2024-盈利预测-市盈率"].mean(),
            }
        }

        # 返回易于阅读的字符串
        result = [
            f"2024年盈利预测-收益: 最高值: {stats['2024-盈利预测-收益']['max']}, 最低值: {stats['2024-盈利预测-收益']['min']}, 平均值: {stats['2024-盈利预测-收益']['mean']}",
            f"2024年盈利预测-市盈率: 最高值: {stats['2024-盈利预测-市盈率']['max']}, 最低值: {stats['2024-盈利预测-市盈率']['min']}, 平均值: {stats['2024-盈利预测-市盈率']['mean']}"
        ]

        return "\n".join(result)

    def get_financial_forecast_summary(self) -> dict:
        """
        获取最近一个财报发行日期的业绩预告数据摘要.返回值Dict[symbol,str]
        
        返回值:
            一个字典，键是股票代码，值是描述性的字符串，包含以下信息的统计：
            - 股票简称
            - 预测指标
            - 业绩变动
            - 预测数值
            - 业绩变动幅度
            - 业绩变动原因
            - 预告类型
            - 上年同期值
            - 公告日期
        """
        date = self.get_latest_financial_report_date()

        # 检查缓存是否存在
        if date in self.forecast_cache:
            return self.forecast_cache[date]
        
        # 获取数据
        data = ak.stock_yjyg_em(date=date)
        
        # 生成描述性字符串的字典
        summary_dict = {}
        for index, row in data.iterrows():
            description = (
                f"股票简称: {row['股票简称']}, "
                f"预测指标: {row['预测指标']}, "
                f"业绩变动: {row['业绩变动']}, "
                f"预测数值: {row['预测数值']}元, "
                f"业绩变动幅度: {row['业绩变动幅度']}%, "
                f"业绩变动原因: {row['业绩变动原因']}, "
                f"预告类型: {row['预告类型']}, "
                f"上年同期值: {row['上年同期值']}元, "
                f"公告日期: {row['公告日期']}"
            )
            summary_dict[row['股票代码']] = description
        
        # 缓存结果
        self.forecast_cache[date] = summary_dict
        
        return summary_dict

    def get_financial_report_summary(self) -> dict:
        """
        获取最近一个财报发行日期的业绩报表数据摘要.返回值Dict[symbol,str]
        
        返回值:
            一个字典，键是股票代码，值是描述性的字符串，包含以下信息的统计：
            - 股票简称
            - 每股收益
            - 营业收入
            - 营业收入同比增长
            - 营业收入季度环比增长
            - 净利润
            - 净利润同比增长
            - 净利润季度环比增长
            - 每股净资产
            - 净资产收益率
            - 每股经营现金流量
            - 销售毛利率
            - 所处行业
            - 最新公告日期
        """
        date = self.get_latest_financial_report_date()

        # 检查缓存是否存在
        if date in self.report_cache:
            return self.report_cache[date]
        
        # 获取数据
        data = ak.stock_yjbb_em(date=date)
        
        # 生成描述性字符串的字典
        summary_dict = {}
        for index, row in data.iterrows():
            description = (
                f"股票简称: {row['股票简称']}, "
                f"每股收益: {row['每股收益']}元, "
                f"营业收入: {row['营业收入-营业收入']}元, "
                f"营业收入同比增长: {row['营业收入-同比增长']}%, "
                f"营业收入季度环比增长: {row['营业收入-季度环比增长']}%, "
                f"净利润: {row['净利润-净利润']}元, "
                f"净利润同比增长: {row['净利润-同比增长']}%, "
                f"净利润季度环比增长: {row['净利润-季度环比增长']}%, "
                f"每股净资产: {row['每股净资产']}元, "
                f"净资产收益率: {row['净资产收益率']}%, "
                f"每股经营现金流量: {row['每股经营现金流量']}元, "
                f"销售毛利率: {row['销售毛利率']}%, "
                f"所处行业: {row['所处行业']}, "
                f"最新公告日期: {row['最新公告日期']}"
            )
            summary_dict[row['股票代码']] = description
        
        # 缓存结果
        self.report_cache[date] = summary_dict
        
        return summary_dict

    def get_top_holdings_by_market(self, market: Literal["北向", "沪股通", "深股通"] = "北向", indicator: Literal["今日排行", "3日排行", "5日排行", "10日排行", "月排行", "季排行", "年排行"] = "月排行") -> dict:
        """
        获取指定市场的持股个股排行，并返回格式化后的结果。参数： market:str="北向" indicator="月排行"  返回值Dict[symbol,str]

        参数:
            market (str): 市场类型，选择 "北向", "沪股通", "深股通" 之一。默认值为 "北向"。
            indicator (str): 排行时间范围，选择 "今日排行", "3日排行", "5日排行", "10日排行", "月排行", "季排行", "年排行" 之一。默认值为 "月排行"。

        返回:
            dict: 键为股票代码，值为该股票的详细信息，格式化为易于阅读的字符串。

        示例:
        >>> get_top_holdings_by_market(market="沪股通", indicator="月排行")
        {'000001': '名称: 平安银行, 今日收盘价: 10.5, 今日涨跌幅: 1.2%, ...', ...}
        """
        # 获取数据
        df = ak.stock_hsgt_hold_stock_em(indicator=indicator, market=market)

        # 处理数据，将每行数据转换为易于阅读的字符串
        result = {}
        for _, row in df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"今日收盘价: {row['今日收盘价']}, "
                f"今日涨跌幅: {row['今日涨跌幅']}%, "
                f"今日持股-股数: {row['今日持股-股数']}万, "
                f"今日持股-市值: {row['今日持股-市值']}万, "
                f"今日持股-占流通股比: {row['今日持股-占流通股比']}%, "
                f"今日持股-占总股本比: {row['今日持股-占总股本比']}%, "
                f"增持估计-股数: {row['增持估计-股数']}万, "
                f"增持估计-市值: {row['增持估计-市值']}万, "
                f"增持估计-市值增幅: {row['增持估计-市值增幅']}%, "
                f"增持估计-占流通股比: {row['增持估计-占流通股比']}‰, "
                f"增持估计-占总股本比: {row['增持估计-占总股本比']}‰, "
                f"所属板块: {row['所属板块']}, "
                f"日期: {row['日期']}"
            )
            result[row['代码']] = stock_info

        return result

    def get_stock_comments_summary(self) -> dict:
        """
        获取东方财富网-数据中心-特色数据-千股千评数据摘要.返回值Dict[symbol,str]
        
        返回值:
            一个字典，键是股票代码，值是描述性的字符串，包含以下信息的统计：
            - 名称
            - 最新价
            - 涨跌幅
            - 换手率
            - 市盈率
            - 主力成本
            - 机构参与度
            - 综合得分
            - 上升
            - 目前排名
            - 关注指数
            - 交易日
        """
        # 检查缓存是否存在
        if "stock_comments" in self.comment_cache:
            return self.comment_cache["stock_comments"]
        
        # 获取数据
        data = ak.stock_comment_em()
        
        # 生成描述性字符串的字典
        summary_dict = {}
        for index, row in data.iterrows():
            description = (
                f"名称: {row['名称']}, "
                f"最新价: {row['最新价']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"换手率: {row['换手率']}%, "
                f"市盈率: {row['市盈率']}, "
                f"主力成本: {row['主力成本']}, "
                f"机构参与度: {row['机构参与度']}%, "
                f"综合得分: {row['综合得分']}, "
                f"上升: {row['上升']}, "
                f"目前排名: {row['目前排名']}, "
                f"关注指数: {row['关注指数']}, "
                f"交易日: {row['交易日']}"
            )
            summary_dict[row['代码']] = description
        
        # 缓存结果
        self.comment_cache["stock_comments"] = summary_dict
        
        return summary_dict

    def get_stock_comments_dataframe(self)->pd.DataFrame:
        """
        千股千评。返回DataFrame
        返回值：
            名称	类型	描述
            序号	int64	-
            代码	object	-
            名称	object	-
            最新价	float64	-
            涨跌幅	float64	-
            换手率	float64	注意单位: %
            市盈率	float64	-
            主力成本	float64	-
            机构参与度	float64	-
            综合得分	float64	-
            上升	int64	注意: 正负号
            目前排名	int64	-
            关注指数	float64	-
            交易日	float64	-
        """
        return ak.stock_comment_em()

    def get_main_business_description(self, symbol: str) -> str:
        """
        获取同花顺-主营介绍的数据，并返str
        
        输入参数:
            symbol (str): 股票代码
            
        返回值:
            一个描述性的字符串，包含以下信息的统计：
            - 股票代码
            - 主营业务
            - 产品类型
            - 产品名称
            - 经营范围
        """
        # 获取数据
        data = ak.stock_zyjs_ths(symbol=symbol)
        
        if data.empty:
            return f"未找到股票代码 {symbol} 的主营介绍数据。"
        
        row = data.iloc[0]
        description = (
            f"股票代码: {row['股票代码']}\n"
            f"主营业务: {row['主营业务']}\n"
            f"产品类型: {row['产品类型']}\n"
            f"产品名称: {row['产品名称']}\n"
            f"经营范围: {row['经营范围']}"
        )
        
        return description

    def get_mainbussiness_more(self,symbol)->pd.DataFrame:
        """
        主营构成 返回DataFrame
        输入参数:
            symbol:str  股票代码
        返回值:
            名称	类型	描述
            股票代码	object	-
            报告日期	object	-
            分类类型	object	-
            主营构成	int64	-
            主营收入	float64	注意单位: 元
            收入比例	float64	-
            主营成本	float64	注意单位: 元
            成本比例	float64	-
            主营利润	float64	注意单位: 元
            利润比例	float64	-
            毛利率	float64	-
        """
        return ak.stock_zygc_em(symbol=symbol)

    def get_mainbussiness_mid(self,symbol:str)->pd.DataFrame:
        """
        主营构成.返回DataFrame
        输入参数:
            symbol:str  股票代码
        返回值:
            名称	类型	描述
            报告期	object	-
            内容	object	-
        """
        return ak.stock_zygc_ym(symbol=symbol)

    def get_manager_talk(self,symbol:str)->pd.DataFrame:
        """
        管理层讨论与分析.返回DataFrame
        输入参数:
            symbol:str  股票代码
        返回值:
            名称	类型	描述
            报告期	object	-
            内容	object	-
        """
        return ak.stock_mda_ym(symbol)

    def get_historical_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        日线数据 参数symbol: str, start_date: str, end_date: st  返回DataFrame
        返回值：Dict[symbol,list]
        list=名称	类型	描述
            日期	object	交易日
            股票代码	object	不带市场标识的股票代码
            开盘	float64	开盘价
            收盘	float64	收盘价
            最高	float64	最高价
            最低	float64	最低价
            成交量	int64	注意单位: 手
            成交额	float64	注意单位: 元
            振幅	float64	注意单位: %
            涨跌幅	float64	注意单位: %
            涨跌额	float64	注意单位: 元
            换手率	float64	注意单位: %
        """
        return ak.stock_zh_a_hist(symbol=symbol,period="daily", start_date=start_date, end_date=end_date)

    def get_code_name(self) -> Dict[str, str]:
        """
        名称和代码的字典，用代码查名称。返回值: Dict[代码,名称]
        
        如果根据代码获取股票名称可以这样：
        name = stock_data_provider.get_code_name()[symbol]
        """
        if self.code_name_list and len(self.code_name_list)>0:
            return self.code_name_list  

        spot = ak.stock_info_a_code_name()
        for index, row in spot.iterrows():
            self.code_name_list[row["code"]] = row["name"]

    def get_news_updates(self, symbols: List[str],since_time: datetime) -> Dict[str, List[Dict]]:
        """
        个股新闻更新.返回值Dict[symbol,str]
        返回值: Dict[symbol,list]
        list=名称	类型	描述
            关键词	object	-
            新闻标题	object	-
            新闻内容	object	-
            发布时间	object	-
            文章来源	object	-
            新闻链接	object	-
        """
        result = {}
        for symbol in symbols:
            news = ak.stock_news_em(symbol=symbol)
            news = news[news["发布时间"] > since_time]
            result[symbol] = news.to_dict(orient="list")

    def get_market_news_300(self) -> List[str]:
        """
        获取财联社最新300条新闻，并将其格式化为字符串列表。
        备注：这个函数一次获取的信息很多，无法让LLM一次处理，需要调用 summarizer_news(news,query) 来蒸馏提取内容

        返回值:
            List[str]: 每个元素是一个格式化的字符串，包含新闻的标题、内容、发布日期和发布时间。

        字符串格式:
            "标题: {标题}, 内容: {内容}, 发布日期: {发布日期}, 发布时间: {发布时间}"
        """
        # 获取新闻数据并转换为字典
        news_data = ak.stock_info_global_cls().to_dict(orient="list")
        
        # 提取新闻数据，并将其格式化为字符串列表
        formatted_news_list = [
            f"标题: {title}, 内容: {content}, 发布日期: {publish_date}, 发布时间: {publish_time}"
            for title, content, publish_date, publish_time in zip(
                news_data.get("标题", []),
                news_data.get("内容", []),
                news_data.get("发布日期", []),
                news_data.get("发布时间", [])
            )
        ]
        
        return formatted_news_list

    def get_stock_minute(self,symbol:str, period='1'):
        """
        个股分钟数据 参数symbol:str  返回值DataFrame
        输入参数：
            symbol:str 股票代码
            period:str 周期，默认为1，可选值：1,5,15,30,60
        返回值:
            名称	类型	描述
            day	object	-
            open	float64	-
            high	float64	-
            low	float64	-
            close	float64	-
            volume	float64	-
        """
        return ak.stock_zh_a_minute(symbol=symbol, period=period)

    def get_index_data(self, index_symbols: List[str],start_date:str,end_date:str) -> Dict[str, pd.DataFrame]:
        """
        获取指数数据,参数index_symbols: List[str]  返回值Dict[symbol,DataFrame]
        """
        result = {}
        for index in index_symbols:
            data = ak.index_zh_a_hist(symbol=index,period="daily",start_date=start_date,end_date=end_date)
            result[index] = data
        return result
    
    def get_stock_news(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        获取个股新闻。参数symbols: List[str] 返回值Dict[symbol,str]
        输入参数:
            symbols: List[str]  股票代码列表
        返回值:
            名称	类型	描述
            关键词	object	-
            新闻标题	object	-
            新闻内容	object	-
            发布时间	object	-
            文章来源	object	-
            新闻链接	object	-
        """
        result = {}
        for symbol in symbols:
            news = ak.stock_news_em(symbol=symbol)
            
            result[symbol] = news.to_dict(orient="list")
    
    def get_stock_info(self,symbol: str) -> str:
        """
        查询指定股票代码的个股信息，参数symbol: str  返回str。

        参数:
        symbol (str): 股票代码，例如 "603777"。

        返回:
        str: 个股信息的格式化字符串，包括总市值、流通市值、行业、上市时间、股票代码、股票简称、总股本和流通股本。
        """

        # 获取个股信息数据框
        stock_info_df = ak.stock_individual_info_em(symbol=symbol)

        # 将数据转换为可读的字符串格式
        stock_info_str = "\n".join([f"{row['item']}: {row['value']}" for _, row in stock_info_df.iterrows()])
        
        return stock_info_str

    def get_realtime_stock_data(self,symbol: str) -> str:
        """
        查询指定证券代码的最新行情数据，参数symbol:str 返回str。

        参数:
        symbol (str): 证券代码，可以是 A 股个股代码，A 股场内基金代码，A 股指数，美股代码, 美股指数，例如 "SH600000"。

        返回:
        str: 最新行情数据的格式化字符串，包括代码、现价、涨幅、最高价、最低价、市盈率、成交量等信息。
        """

        # 获取实时行情数据
        stock_spot_df = ak.stock_individual_spot_xq(symbol=symbol)

        # 将数据转换为可读的字符串格式
        stock_spot_str = "\n".join([f"{row['item']}: {row['value']}" for _, row in stock_spot_df.iterrows()])
        
        return stock_spot_str

    def get_full_realtime_data(self) -> dict[str, str]:
        """
        获取并格式化当前证券代码列表的实时行情数据。返回值Dict[symbol,str]

        函数将获取证券代码的最新行情数据，并将其结果转换为格式化的字符串，存储在字典中。

        返回:
        dict[str, str]: 每个证券代码及其对应的最新行情数据的格式化字符串，包含代码、现价、涨幅、最高价、最低价、市盈率、成交量等信息。
        """

        # 获取实时行情数据
        stock_spot_df = ak.stock_individual_spot_xq()

        # 初始化一个字典来存储结果
        formatted_data = {}

        # 遍历实时数据的每一行
        for _, row in stock_spot_df.iterrows():
            symbol = row['symbol']
            
            # 将数据转换为可读的字符串格式
            stock_spot_str = "\n".join([f"{item}: {value}" for item, value in row.items() if item != 'symbol'])

            # 存储在字典中
            formatted_data[symbol] = stock_spot_str

        return formatted_data

    def get_stock_announcements(self,symbols: List[str], date: str = None) -> Dict[str, List[str]]:
        """
        获取指定日期内指定股票代码的公告信息。参数symbols: List[str] 返回值Dict[symbol,List[str]]

        参数:
        symbols (List[str]): 股票代码列表。
        date (str, 可选): 查询的日期，格式为 "YYYY-MM-DD"。如果未指定，则使用最近的交易日期。

        返回:
        Dict[str, List[str]]: 一个字典，其中键是股票代码，值是该股票在指定日期内发布的公告列表。
        """
        result = {}
        if not date:
            date = self.get_last_trade_date()
        df = ak.stock_gsrl_gsdt_em(date=date)
        for symbol in symbols:
            result[symbol] = []
            filtered_df = df[df['股票代码'] == symbol]
            for row in filtered_df.itertuples():
                result[symbol].append(row["具体事项"])
        return result

    def stock_info_global_ths(self):
        """
        同花顺财经 20条,返回DataFrame
        返回值：
            名称	类型	描述
            标题	object	-
            内容	object	-
            发布时间	object	-
            链接	object	-
        """
        return ak.stock_info_global_ths()

    def stock_info_global_futu(self):
        """
        富途财经 50条 ,返回DataFrame
        返回值：
            名称	类型	描述
            标题	object	-
            内容	object	-
            发布时间	object	-
            链接	object	-
        """
        return ak.stock_info_global_futu()

    def stock_info_global_sina(self):
        """
        新浪财经 20条 ,返回DataFrame
        返回值：
        名称	类型	描述
        时间	object	-
        内容	object	-
        """
        return ak.stock_info_global_sina()

    def stock_info_global_em(self):
        """
        东方财富 200条 ,返回DataFrame
        返回值：
            名称	类型	描述
            标题	object	-
            摘要	object	-
            发布时间	object	-
            链接	object	-
        """
        return ak.stock_info_global_em()

    def summarize_historical_data(self, symbols: List[str]) -> dict:
        """
        汇总多个股票的历史数据。 参数symbols: List[str] 返回Dict[symbol,str]
        
        输入参数:
            symbols: List[str] 股票代码列表
            
        返回值:
            一个字典，键是股票代码，值是描述性的字符串。
        """
        summary_dict = {}
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")

        for symbol in symbols:
            # 检查缓存
            if symbol in self.historical_data_cache:
                df = self.historical_data_cache[symbol]
            else:
                df = self.get_historical_daily_data(symbol, start_date, end_date)
                self.historical_data_cache[symbol] = df
            
            if df.empty:
                summary_dict[symbol] = "未找到数据"
                continue

            # 计算常用技术指标
            df['MA20'] = ta.trend.sma_indicator(df['收盘'], window=20)
            df['MA50'] = ta.trend.sma_indicator(df['收盘'], window=50)
            df['RSI'] = ta.momentum.rsi(df['收盘'], window=14)
            macd = ta.trend.MACD(df['收盘'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            bb = ta.volatility.BollingerBands(df['收盘'], window=20, window_dev=2)
            df['BB_upper'] = bb.bollinger_hband()
            df['BB_lower'] = bb.bollinger_lband()

            # 获取数据统计
            latest_close = df['收盘'].iloc[-1]
            highest_close = df['收盘'].max()
            lowest_close = df['收盘'].min()
            avg_volume = df['成交量'].mean()
            latest_rsi = df['RSI'].iloc[-1]
            latest_macd = df['MACD'].iloc[-1]
            latest_macd_signal = df['MACD_signal'].iloc[-1]
            bb_upper = df['BB_upper'].iloc[-1]
            bb_lower = df['BB_lower'].iloc[-1]

            # 生成描述性的字符串
            description = (
                f"股票代码: {symbol}\n"
                f"最新收盘价: {latest_close}\n"
                f"最近半年内最高收盘价: {highest_close}\n"
                f"最近半年内最低收盘价: {lowest_close}\n"
                f"最近半年平均成交量: {avg_volume}\n"
                f"最新RSI(14): {latest_rsi}\n"
                f"最新MACD: {latest_macd}\n"
                f"最新MACD信号线: {latest_macd_signal}\n"
                f"布林带上轨: {bb_upper}\n"
                f"布林带下轨: {bb_lower}\n"
                f"MA20: {df['MA20'].iloc[-1]}\n"
                f"MA50: {df['MA50'].iloc[-1]}"
            )
            
            summary_dict[symbol] = description
        
        return summary_dict

    def summarize_historical_index_data(self, index_symbols: List[str]) -> dict:
        """
        汇总多个指数的历史数据， 参数symbols: List[str] 返回Dict[symbol,str]
        备注：上证指数：000001;上证50:000016;上证300：000300；中证1000：000852；中证500：000905

        输入参数:
            index_symbols: List[str] 指数代码列表

        返回值:
            一个字典，键是指数代码，值是描述性的字符串。
        """
        summary_dict = {}
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")

        for symbol in index_symbols:
            # 检查缓存
            if symbol in self.historical_data_cache:
                df = self.historical_data_cache[symbol]
            else:
                df = self.get_index_data([symbol], start_date, end_date)[symbol]
                self.historical_data_cache[symbol] = df
            
            if df.empty:
                summary_dict[symbol] = "未找到数据"
                continue

            # 获取数据统计
            latest_close = df['收盘'].iloc[-1]
            highest_close = df['收盘'].max()
            lowest_close = df['收盘'].min()
            avg_volume = df['成交量'].mean()
            std_dev = df['收盘'].std()
            median_close = df['收盘'].median()
            avg_close = df['收盘'].mean()
            return_rate = (df['收盘'].iloc[-1] - df['收盘'].iloc[0]) / df['收盘'].iloc[0] * 100

            # 生成描述性的字符串
            description = (
                f"指数代码: {symbol}\n"
                f"最新收盘价: {latest_close}\n"
                f"最近半年内最高收盘价: {highest_close}\n"
                f"最近半年内最低收盘价: {lowest_close}\n"
                f"最近半年平均成交量: {avg_volume}\n"
                f"收盘价标准差: {std_dev}\n"
                f"收盘价中位数: {median_close}\n"
                f"最近半年平均收盘价: {avg_close}\n"
                f"半年累计回报率: {return_rate:.2f}%"
            )
            
            summary_dict[symbol] = description
        
        return summary_dict

    def get_index_components(self, index_symbol: str) -> list:
        """
        获取指定指数的最新成分股代码列表。参数 index_symbol: str 返回 list

        参数:
            index_symbol (str): 指数代码，例如 "000300" 表示沪深300指数。

        返回:
            list: 包含指定指数所有成分股代码的列表。
        """
        try:
            df = ak.index_stock_cons(index_symbol)
            stock_codes = df["品种代码"].to_list()
            return stock_codes
        except Exception as e:
            print(f"获取成分股数据时出错: {e}")
            return []
        
    def get_function_docstring(self, function_name: str) -> str:
        """
        获取指定函数的__docstring__。

        参数:
            function_name (str): 函数名称（字符串形式）。

        返回:
            str: 该函数的__docstring__，如果函数不存在或没有__docstring__，返回提示信息。
        """
        function = getattr(self, function_name, None)
        if function is None:
            return f"函数 '{function_name}' 不存在。"
        
        docstring = function.__doc__
        if docstring:
            return docstring.strip()
        else:
            return f"函数 '{function_name}' 没有 __docstring__。"

    def select_stock_by_query(self, query: str):
        """
        根据用户的自然语言查询来筛选股票数据。

        参数:
        query (str): 用户的自然语言查询，描述了股票筛选的条件。

        返回:
        dict: 一个字典，其中键是股票代码，值是该股票的其他信息字符串。

        抛出:
        ValueError: 如果无法从LLM响应中提取Python代码。
        Exception: 如果代码执行失败或结果格式不正确。

        示例:
        >>> select_stock_by_query("5分钟涨跌幅大于1%的股票")
        {'000001': '名称: 平安银行, 现价: 10.5, 涨跌幅: 1.2%, ...', ...}
        """
        df = ak.stock_zh_a_spot_em()
        df_summary = self.data_summarizer.get_data_summary(df)
        global_vars={}
        global_vars["df"]=df
        prompt = f"""
            需要处理的请求：
            {query}

            需要处理的变量名：
            df

            df的摘要如下：
            {df_summary}

            生成一段python代码，完成query的筛选要求
            要求：
            1. 代码用```python   ```包裹
            2. 请求应该跟df的数据过滤相关，如果不相关，返回 
            ```python
            result={{}}
            ```
            3. 对df过滤后，需要把过滤的行处理为Dict[str,str]，赋值给result
            4. 根据query的内容对df进行过滤，例如：
                - 查询："5分钟涨跌幅大于1%的股票"
                - 代码
                ```python
                df_filtered = df[df['5分钟涨跌']>1]
                result = {{}}
                for _, row in df_filtered.iterrows():
                    result[row['代码']] = ", ".join([f"{{col}}: {{row[col]}}" for col in df_filtered.columns if col != '代码'])
                ```
            5. 确保 result 是一个字典，键为股票代码，值为该股票的其他信息字符串
            6. 不要使用任何不在 df 中的列名
            7. 使用名字查询的时候，注意使用模糊查询的方法，避免名字不精确查询不到数据
        """
        new_prompt = prompt
        while True:
            response = self.llm_client.one_chat(new_prompt)
            try:
                code = self._extract_code(response)
                if not code:
                    raise ValueError("No Python code found in the response, 请提供python代码，并包裹在```python  ```之中")
                
                execute_result = self.code_runner.run(code,global_vars=global_vars)
                if execute_result["error"]:
                    raise execute_result["error"]
                if "result" not in execute_result["updated_vars"]:
                    raise Exception("代码执行完以后，没有检测到result变量，必须把结果保存在result变量之中")
                if not isinstance(execute_result["updated_vars"]["result"], dict):
                    raise Exception("result必须是字典格式，请修改代码，把结果保存于字典格式的dict")
                
                return execute_result["updated_vars"]["result"]
            except Exception as e:
                fix_prompt = f"""
                刚刚用下面的提示词
                {prompt}

                生成了下面的代码
                {code}

                发生了下面的错误：
                {str(e)}

                请帮我修正代码，代码要求不变，输出的代码包裹在```python  ```之中
                修正代码不用加任何解释
                """
                new_prompt = fix_prompt

    def _extract_code(self, response):
        """
        从LLM的响应中提取Python代码。

        参数:
        response (str): LLM的完整响应文本

        返回:
        str: 提取出的Python代码。如果没有找到代码，返回空字符串。
        """
        # 使用正则表达式查找被 ```python 和 ``` 包围的代码块
        code_pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(code_pattern, response, re.DOTALL)

        if matches:
            # 返回找到的第一个代码块
            return matches[0].strip()
        else:
            # 如果没有找到代码块，可以选择抛出异常或返回空字符串
            # 这里选择返回空字符串
            return ""

    def get_concept_board_components(self, symbol: str = '车联网') -> dict:
        """
        获取指定概念板块的成分股。参数symbol: str = '车联网' 返回值 dict[symbol,str]

        参数:
            symbol (str): 概念板块名称，例如 "车联网"。可以通过调用 ak.stock_board_concept_name_em() 查看东方财富-概念板块的所有行业名称。

        返回:
            dict: 键为成分股代码，值为该成分股的详细信息，格式化为易于阅读的字符串。
        """
        df = ak.stock_board_concept_cons_em(symbol)

        # 处理数据，将每行数据转换为易于阅读的字符串
        result = {}
        for _, row in df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"最新价: {row['最新价']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"涨跌额: {row['涨跌额']}, "
                f"成交量: {row['成交量']}手, "
                f"成交额: {row['成交额']}, "
                f"振幅: {row['振幅']}%, "
                f"最高: {row['最高']}, "
                f"最低: {row['最低']}, "
                f"今开: {row['今开']}, "
                f"昨收: {row['昨收']}, "
                f"换手率: {row['换手率']}%, "
                f"市盈率-动态: {row['市盈率-动态']}, "
                f"市净率: {row['市净率']}"
            )
            result[row['代码']] = stock_info

        return result

    def select_stocks_by_concept_board_query(self, query: str) -> dict:
        """
        根据用户的自然语言查询来筛选概念板块中的股票数据。参数 query:str 返回dict[symbol,str]

        参数:
        query (str): 用户的自然语言查询，描述了概念板块筛选的条件。

        返回:
        dict: 一个字典，其中键是股票代码，值是该股票的其他信息字符串。

        抛出:
        ValueError: 如果无法从LLM响应中提取Python代码。
        Exception: 如果代码执行失败或结果格式不正确。

        示例:
        >>> select_stocks_by_concept_board_query("涨幅超过2%的板块")
        {'000001': '名称: 平安银行, 现价: 10.5, 涨跌幅: 1.2%, ...', ...}
        """
        # 获取所有概念板块数据
        df_concepts = ak.stock_board_concept_name_em()
        df_summary = self.data_summarizer.get_data_summary(df_concepts)
        global_vars ={"df_concepts":df_concepts}
        prompt = f"""
            需要处理的请求：
            {query}

            需要处理的变量名：
            df_concepts

            df_concepts的摘要如下：
            {df_summary}

            生成一段python代码，完成query的筛选要求
            要求：
            1. 代码用```python   ```包裹
            2. 请求应该跟df_concepts的数据过滤相关，如果不相关，返回 
            ```python
            result = []
            ```
            3. 对df_concepts过滤后，需要把符合条件的板块名提取出来，赋值给result
            4. 根据query的内容对df_concepts进行过滤，例如：
                - 查询："涨幅超过2%的板块"
                - 代码
                ```python
                df_filtered = df_concepts[df_concepts['涨跌幅']>2]
                result = df_filtered['板块名称'].tolist()
                ```
            5. 确保 result 是一个列表，其中包含符合条件的板块名称
            6. 不要使用任何不在 df_concepts 中的列名
            7. 示例代码（根据实际情况调整）：
            ```python
            import re
            keywords = ['科技', '电子', '信息', '通信', '互联网', '软件','人工智能','芯片']
            pattern = '|'.join(keywords)
            mask = df_concepts['板块名称'].str.contains(pattern, case=False, na=False)
            result = df_concepts[mask]['板块名称'].tolist()
            ```
            8. 如果没有完全匹配的结果，考虑返回部分匹配或相关的结果
            9. 添加注释解释你的匹配逻辑
        """
        new_prompt = prompt
        while True:
            response = self.llm_client.one_chat(new_prompt)
            try:
                code = self._extract_code(response)
                if not code:
                    raise ValueError("No Python code found in the response, 请提供python代码，并包裹在```python  ```之中")
                
                execute_result = self.code_runner.run(code,global_vars=global_vars)
                if execute_result["error"]:
                    raise execute_result["error"]
                if "result" not in execute_result["updated_vars"]:
                    raise Exception("代码执行完以后，没有检测到result变量，必须把结果保存在result变量之中")
                if not isinstance(execute_result["updated_vars"]["result"], list):
                    raise Exception("result必须是列表格式，请修改代码，确保返回的是板块名称的列表")
                
                # 获取成分股
                selected_boards = execute_result["updated_vars"]["result"]
                all_stocks = {}
                for board_name in selected_boards:
                    stocks = self.get_concept_board_components(board_name)
                    all_stocks.update(stocks)
                
                return all_stocks
            except Exception as e:
                fix_prompt = f"""
                刚刚用下面的提示词
                {prompt}

                生成了下面的代码
                {code}

                发生了下面的错误：
                {str(e)}

                请帮我修正代码，代码要求不变，输出的代码包裹在```python  ```之中
                修正代码不用加任何解释
                """
                new_prompt = fix_prompt

    def get_board_industry_components(self, symbol: str) -> dict:
        """
        获取指定行业板块的成分股。参数 symbol: str 返回 Dict[symbol,str]

        参数:
            symbol (str): 行业板块名称，例如 "小金属"。可以通过调用 ak.stock_board_industry_name_em() 查看东方财富-行业板块的所有行业名称。

        返回:
            dict: 键为成分股代码，值为该成分股的详细信息，格式化为易于阅读的字符串。
        """
        df = ak.stock_board_industry_cons_em(symbol)

        # 处理数据，将每行数据转换为易于阅读的字符串
        result = {}
        for _, row in df.iterrows():
            stock_info = (
                f"名称: {row['名称']}, "
                f"最新价: {row['最新价']}, "
                f"涨跌幅: {row['涨跌幅']}%, "
                f"涨跌额: {row['涨跌额']}, "
                f"成交量: {row['成交量']}手, "
                f"成交额: {row['成交额']}, "
                f"振幅: {row['振幅']}%, "
                f"最高: {row['最高']}, "
                f"最低: {row['最低']}, "
                f"今开: {row['今开']}, "
                f"昨收: {row['昨收']}, "
                f"换手率: {row['换手率']}%, "
                f"市盈率-动态: {row['市盈率-动态']}, "
                f"市净率: {row['市净率']}"
            )
            result[row['代码']] = stock_info

        return result

    def select_stocks_by_industry_board_query(self, query: str) -> dict:
        """
        根据用户的自然语言查询来筛选行业板块中的股票数据。参数 query: str 返回 Dict[symbol,str]

        参数:
        query (str): 用户的自然语言查询，描述了行业板块筛选的条件。

        返回:
        dict: 一个字典，其中键是股票代码，值是该股票的其他信息字符串。

        抛出:
        ValueError: 如果无法从LLM响应中提取Python代码。
        Exception: 如果代码执行失败或结果格式不正确。

        示例:
        >>> select_stocks_by_industry_board_query("涨幅超过2%的板块")
        {'000001': '名称: 平安银行, 现价: 10.5, 涨跌幅: 1.2%, ...', ...}
        """
        # 获取所有行业板块数据
        df_industries = ak.stock_board_industry_name_em()
        df_summary = self.data_summarizer.get_data_summary(df_industries)
        global_vars={"df_industries":df_industries}
        prompt = f"""
            需要处理的请求：
            {query}

            需要处理的变量名：
            df_industries

            df_industries的摘要如下：
            {df_summary}

            生成一段python代码，完成query的筛选要求
            要求：
            1. 代码用```python   ```包裹
            2. 请求应该跟df_industries的数据过滤相关，如果不相关，返回 
            ```python
            result = []
            ```
            3. 对df_industries过滤后，需要把符合条件的板块名提取出来，赋值给result
            4. 根据query的内容对df_industries进行过滤，考虑以下几点：
            - 使用更灵活的匹配方式，如模糊匹配或相关词匹配
            - 考虑同义词或相关词，例如"科技"可能与"电子"、"信息"、"通信"等相关
            - 可以使用正则表达式进行更复杂的匹配
            5. 确保 result 是一个列表，其中包含符合条件的板块名称
            6. 不要使用任何不在 df_industries 中的列名
            7. 示例代码（根据实际情况调整）：
            ```python
            import re
            keywords = ['科技', '电子', '信息', '通信', '互联网', '软件','人工智能','芯片']
            pattern = '|'.join(keywords)
            mask = df_industries['板块名称'].str.contains(pattern, case=False, na=False)
            result = df_industries[mask]['板块名称'].tolist()
            ```
            8. 如果没有完全匹配的结果，考虑返回部分匹配或相关的结果
            9. 添加注释解释你的匹配逻辑
        """
        new_prompt = prompt
        while True:
            response = self.llm_client.one_chat(new_prompt)
            try:
                code = self._extract_code(response)
                if not code:
                    raise ValueError("No Python code found in the response, 请提供python代码，并包裹在```python  ```之中")
                
                execute_result = self.code_runner.run(code,global_vars=global_vars)
                if execute_result["error"]:
                    raise execute_result["error"]
                if "result" not in execute_result["updated_vars"]:
                    raise Exception("代码执行完以后，没有检测到result变量，必须把结果保存在result变量之中")
                if not isinstance(execute_result["updated_vars"]["result"], list):
                    raise Exception("result必须是列表格式，请修改代码，确保返回的是板块名称的列表")
                
                # 获取成分股
                selected_boards = execute_result["updated_vars"]["result"]
                all_stocks = {}
                for board_name in selected_boards:
                    stocks = self.get_board_industry_components(board_name)
                    all_stocks.update(stocks)
                
                return all_stocks
            except Exception as e:
                fix_prompt = f"""
                刚刚用下面的提示词
                {prompt}

                生成了下面的代码
                {code}

                发生了下面的错误：
                {str(e)}

                请帮我修正代码，代码要求不变，输出的代码包裹在```python  ```之中
                修正代码不用加任何解释
                """
                new_prompt = fix_prompt

    def select_by_query(self, 
                        data_source: Union[pd.DataFrame, Callable[[], pd.DataFrame]], 
                        query: str, 
                        result_type: str = 'dict', 
                        key_column: str = None, 
                        value_columns: List[str] = None) -> Union[Dict[str, str], List[str]]:
        """
        根据用户的自然语言查询来筛选数据。

        参数:
        data_source (Union[pd.DataFrame, Callable[[], pd.DataFrame]]): 
            数据源，可以是一个DataFrame或者是返回DataFrame的无参数函数。
        query (str): 用户的自然语言查询，描述了筛选的条件。
        result_type (str): 结果类型，'dict' 或 'list'。默认为 'dict'。
        key_column (str): 如果result_type为'dict'，这个参数指定作为字典键的列名。
        value_columns (List[str]): 如果result_type为'dict'，这个参数指定作为字典值的列名列表。

        返回:
        Union[Dict[str, str], List[str]]: 
            如果result_type为'dict'，返回一个字典，其中键是key_column指定的列的值，
            值是value_columns指定的列的值组成的字符串。
            如果result_type为'list'，返回一个列表，包含符合条件的行的第一列值。

        抛出:
        ValueError: 如果无法从LLM响应中提取Python代码。
        Exception: 如果代码执行失败或结果格式不正确。

        示例:
        >>> df = pd.DataFrame({'code': ['000001', '000002'], 'name': ['平安银行', '万科A'], 'price': [10.5, 15.2]})
        >>> select_by_query(df, "价格大于12的股票", 'dict', 'code', ['name', 'price'])
        {'000002': '名称: 万科A, 价格: 15.2'}
        >>> select_by_query(df, "价格大于12的股票", 'list')
        ['000002']
        """
        if callable(data_source):
            df = data_source()
        else:
            df = data_source

        df_summary = self.data_summarizer.get_data_summary(df)
        global_vars={"df":df}
        prompt = f"""
            需要处理的请求：
            {query}

            需要处理的变量名：
            df

            df的摘要如下：
            {df_summary}

            生成一段python代码，完成query的筛选要求
            要求：
            1. 代码用```python   ```包裹
            2. 请求应该跟df的数据过滤相关，如果不相关，返回 
            ```python
            result = []
            ```
            3. 对df过滤后，需要把符合条件的行赋值给result
            4. 根据query的内容对df进行过滤，例如：
                - 查询："价格大于12的股票"
                - 代码
                ```python
                result = df[df['price'] > 12]
                ```
            5. 确保 result 是一个DataFrame，包含符合条件的所有行
            6. 不要使用任何不在 df 中的列名
            7. 使用名字查询的时候，注意使用模糊查询的方法，避免名字不精确查询不到数据
        """
        new_prompt = prompt
        while True:
            response = self.llm_client.one_chat(new_prompt)
            try:
                code = self._extract_code(response)
                if not code:
                    raise ValueError("No Python code found in the response, 请提供python代码，并包裹在```python  ```之中")
                
                execute_result = self.code_runner.run(code,global_vars=global_vars)
                if execute_result["error"]:
                    raise execute_result["error"]
                if "result" not in execute_result["updated_vars"]:
                    raise Exception("代码执行完以后，没有检测到result变量，必须把结果保存在result变量之中")
                if not isinstance(execute_result["updated_vars"]["result"], pd.DataFrame):
                    raise Exception("result必须是DataFrame格式，请修改代码，确保返回的是筛选后的DataFrame")
                
                filtered_df = execute_result["updated_vars"]["result"]
                
                if result_type == 'dict':
                    if not key_column or not value_columns:
                        raise ValueError("For dict result type, key_column and value_columns must be specified")
                    return {
                        row[key_column]: ", ".join([f"{col}: {row[col]}" for col in value_columns])
                        for _, row in filtered_df.iterrows()
                    }
                elif result_type == 'list':
                    return filtered_df.iloc[:, 0].tolist()
                else:
                    raise ValueError("Invalid result_type. Must be 'dict' or 'list'")
            
            except Exception as e:
                fix_prompt = f"""
                刚刚用下面的提示词
                {prompt}

                生成了下面的代码
                {code}

                发生了下面的错误：
                {str(e)}

                请帮我修正代码，代码要求不变，输出的代码包裹在```python  ```之中
                修正代码不用加任何解释
                """
                new_prompt = fix_prompt

    def select_by_stock_comments(self, query: str) -> dict:
        """
        根据用户的查询条件筛选千股千评数据。参数query:str 返回Dict[symbol,str]

        此函数使用 akshare 的 stock_comment_em 函数获取千股千评数据，
        然后使用 select_by_query 方法根据用户的查询条件进行筛选。

        参数:
        query (str): 用户的自然语言查询，描述了筛选千股千评数据的条件。

        返回:
        dict: 一个字典，其中键是股票代码，值是该股票的其他信息字符串。
              返回的信息包括：名称、最新价、涨跌幅、换手率、市盈率、主力成本、
              机构参与度、综合得分、排名变化、当前排名、关注指数和交易日。

        示例:
        >>> select_by_stock_comments("综合得分大于80的股票")
        {'000001': '名称: 平安银行, 最新价: 10.5, 涨跌幅: 1.2%, ...', ...}
        """
        # 获取千股千评数据
        df = ak.stock_comment_em()
        
        # 定义要包含在结果中的列
        value_columns = [
            "名称", "最新价", "涨跌幅", "换手率", "市盈率", "主力成本", 
            "机构参与度", "综合得分", "上升", "目前排名", "关注指数", "交易日"
        ]
        
        # 使用 select_by_query 方法进行筛选
        result = self.select_by_query(
            df, 
            query, 
            result_type='dict', 
            key_column="代码", 
            value_columns=value_columns
        )
        
        return result

    def get_baidu_hotrank(self, hour=7, num=20) -> dict:
        """
        获取百度热门股票排行榜。参数  hour=7, num=20 返回 Dict[symbol,str]

        参数:
        hour (int): 获取最近多少小时的数据，默认为7小时。
        num (int): 需要获取的热门股票数量，默认为20。

        返回:
        dict: 键为股票代码，值为格式化的字符串，包含热门股票的详细信息，包括排名。
        """
        # 获取当前日期
        date = datetime.now().strftime("%Y%m%d")
        
        # 获取热门股票列表
        hotlist = self.baidu_news_api.fetch_hotrank(day=date, hour=hour, rn=num)
        
        # 格式化结果
        result = {}
        for rank, item in enumerate(hotlist, 1):  # enumerate从1开始，给每个项目一个排名
            stock_info = (
                f"排名: {rank}\n"  # 添加排名信息
                f"股票名称: {item['name']}\n"
                f"当前价格: {item['price']}\n"
                f"涨跌幅: {item['change']}\n"
                f"所属板块: {item['sector']}\n"
                f"排名变化: {item['rank_change']}\n"
                f"地区: {item['region']}\n"
                f"热度: {item['heat']}\n"
                f"----------------------"
            )
            result[item['code']] = stock_info
        
        return result

    def get_baidu_recommendation(self, hour=7, num=20) -> dict:
        """
        获取百度股票推荐列表。参数  hour=7, num=20 返回 Dict[symbol,str]

        参数:
        hour (int): 获取最近多少小时的数据，默认为7小时。
        num (int): 需要获取的推荐股票数量，默认为20。

        返回:
        dict: 键为股票代码，值为格式化的字符串，包含推荐股票的详细信息。
        """
        # 获取当前日期
        date = datetime.now().strftime("%Y%m%d")
        
        # 获取推荐股票列表
        rlist = self.baidu_news_api.fetch_recommendation_list(day=date, hour=hour, rn=num)
        
        # 格式化结果
        result = {}
        for rank, item in enumerate(rlist, 1):  # enumerate从1开始，给每个项目一个排名
            stock_info = (
                f"排名: {rank}\n"
                f"股票名称: {item['name']}\n"
                f"涨跌幅: {item['change']}\n"
                f"综合热度: {item['heat']}\n"
                f"所属板块: {item['sector_name']}\n"
                f"排名变化: {item['rank_change']}\n"
                f"是否连续上榜: {item['continued_ranking']}\n"
                f"----------------------"
            )
            result[item['code']] = stock_info
        
        return result

    def get_baidu_sentiment_rank(self, num=20) -> dict:
        """
        获取百度股票情绪排名。参数 num=20 返回 Dict[symbol,str]

        参数:
        num (int): 需要获取的股票数量，默认为20。

        返回:
        dict: 键为股票代码，值为格式化的字符串，包含股票的情绪排名信息。
        """
        # 获取情绪排名数据
        sentiment_list = self.baidu_news_api.fetch_sentiment_rank(rn=num)
        
        # 格式化结果
        result = {}
        for rank, item in enumerate(sentiment_list, 1):
            stock_info = (
                f"排名: {rank}\n"
                f"股票名称: {item['name']}\n"
                f"股票代码: {item['code']}\n"
                f"交易所: {item['exchange']}\n"
                f"市场: {item['market']}\n"
                f"所属板块: {item['plate']} ({item['plateCode']})\n"
                f"排名变化: {item['rankDiff']}\n"
                f"比率: {item['ratio']}\n"
                f"热度: {item['heat']}\n"
                f"利好新闻占比: {item['goodNewsPercent']}\n"
                f"中性新闻占比: {item['middleNewsPercent']}\n"
                f"利空新闻占比: {item['badNewsPercent']}\n"
                f"----------------------"
            )
            result[item['code']] = stock_info
        
        return result

    def get_baidu_analysis_rank(self, num=20) -> dict:
        """
        获取百度股票分析排名。参数 num=20 返回 Dict[symbol,str]

        参数:
        num (int): 需要获取的股票数量，默认为20。

        返回:
        dict: 键为股票代码，值为格式化的字符串，包含股票的分析排名信息。
        """
        # 获取分析排名数据
        analysis_list = self.baidu_news_api.fetch_analysis_rank(rn=num)
        
        # 格式化结果
        result = {}
        for rank, item in enumerate(analysis_list, 1):
            stock_info = (
                f"排名: {rank}\n"
                f"股票名称: {item['name']}\n"
                f"股票代码: {item['code']}\n"
                f"市场: {item['market']}\n"
                f"排名变化: {item['rank_change']}\n"
                f"综合得分: {item['synthesis_score']}\n"
                f"技术得分: {item['technology_score']}\n"
                f"资金得分: {item['capital_score']}\n"
                f"市场得分: {item['market_score']}\n"
                f"财务得分: {item['finance_score']}\n"
                f"所属板块: {item['sector']} ({item['sector_code']})\n"
                f"市场类型: {item['market_type']}\n"
                f"----------------------"
            )
            result[item['code']] = stock_info
        
        return result

    def get_baidu_analysis_summary(self, symbol: str) -> str:
        """
        获取百度股票分析摘要。参数 symbol: str 返回 Dict[symbol,str]

        参数:
        symbol (str): 股票代码，例如 '000725'。

        返回:
        str: 格式化的字符串，包含股票的详细分析信息。
        """
        # 确定市场类型
        if symbol.startswith('HK'):
            market = 'hk'
        elif symbol.isalpha() or (symbol.isalnum() and not symbol.isdigit()):
            market = 'us'
        else:
            market = 'ab'  # 所有 A 股

        # 获取分析数据
        analysis_data = self.baidu_news_api.fetch_analysis(code=symbol, market=market)
        
        # 格式化结果
        formatted_analysis = (
            f"股票代码: {symbol}\n"
            f"市场: {'A股' if market == 'ab' else '港股' if market == 'hk' else '美股'}\n\n"
            f"{analysis_data}"
        )
        
        return formatted_analysis

    def get_baidu_stock_news(self, symbol: str, num: int = 20) -> List[str]:
        """
        获取指定股票的百度快讯新闻。 参数 symbol: str, num: int = 20 返回 Dict[symbol,str]

        参数:
        symbol (str): 股票代码，例如 '000725'。
        num (int): 需要获取的新闻数量，默认为20。

        返回:
        List[str]: 包含格式化新闻信息的字符串列表。
        """
        # 获取快讯新闻数据
        news_list = self.baidu_news_api.fetch_express_news(rn=num, code=symbol)
        
        # 格式化结果
        result = []
        for news_item in news_list:
            news_time = news_item['ptime']
            news_info = (
                f"发布时间: {news_time}\n"
                f"标题: {news_item['title']}\n"
                f"内容: {news_item['content']}\n"
                f"标签: {news_item['tag']}\n"
                f"来源: {news_item['provider']}\n"
                f"----------------------"
            )
            result.append(news_info)
        
        return result

    def get_baidu_market_news(self, num: int = 40) -> List[str]:
        """
        获取百度 A 股市场快讯新闻。 参数 num: int = 40 返回 Dict[symbol,str]

        参数:
        num (int): 需要获取的新闻数量，默认为40。

        返回:
        List[str]: 包含格式化新闻信息的字符串列表。
        """
        # 计算需要请求的页数
        pages = (num + 5) // 6  # 每页6条新闻，向上取整
        
        # 获取快讯新闻数据
        news_list = []
        for page in range(pages):
            news_batch = self.baidu_news_api.fetch_express_news_v2(rn=6, pn=page, tag='A股')
            news_list.extend(news_batch)
            if len(news_list) >= num:
                break
        
        # 只保留需要的数量
        news_list = news_list[:num]
        
        # 格式化结果
        result = []
        for news_item in news_list:
            news_time = news_item['ptime']
            news_info = (
                f"发布时间: {news_time}\n"
                f"标题: {news_item['title']}\n"
                f"内容: {news_item['content']}\n"
                f"标签: {news_item['tag']}\n"
                f"来源: {news_item['provider']}\n"
                f"----------------------"
            )
            result.append(news_info)
        
        return result

    def summarizer_news(self, news_source: list[str], query: str="总结市场热点,市场机会,市场风险", max_word: int = 240) -> str:
        """
        对给定的新闻列表进行摘要，根据指定的查询要求生成一个简洁的总结。 参数news_source: list[str], query: str="总结市场热点,市场机会,市场风险", max_word: int = 240 返回值str

        这个函数首先将新闻文本分成较小的块，然后对每个块进行摘要。如果摘要的总长度超过指定的最大字数，
        它会继续进行迭代摘要，直到得到一个不超过最大字数的最终摘要。

        参数:
        news_source (list[str]): 包含新闻文本的字符串列表。每个字符串应该是一条完整的新闻。
        query (str, 可选): 指定摘要的重点或方向。默认为"总结市场热点,市场机会,市场风险"。
        max_word (int, 可选): 最终摘要的最大字数。默认为240。

        返回:
        str: 不超过指定最大字数的新闻摘要。

        示例:
        >>> news = ["今日股市大涨，科技股领涨。", "央行宣布降息，刺激经济增长。", "新能源车企发布新品，股价应声上涨。"]
        >>> summary = stock_data_provider.summarizer_news(news, "分析今日股市表现", 100)
        >>> print(summary)
        """
        def chunk_text(text_list: list[str], max_chars: int = 10000) -> list[str]:
            chunks = []
            current_chunk = ""
            for text in text_list:
                if len(current_chunk) + len(text) <= max_chars:
                    current_chunk += text + " "
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = text + " "
            if current_chunk:
                chunks.append(current_chunk.strip())
            return chunks

        def summarize_chunk(chunk: str, query: str) -> str:
            prompt = f"请根据以下查询要求总结这段新闻内容：\n\n查询：{query}\n\n新闻内容：\n{chunk}\n\n总结："
            return self.llm_client.one_chat(prompt)

        # 将新闻分成不超过10000字符的块
        news_chunks = chunk_text(news_source)
        
        # 对每个块进行摘要
        summaries = [summarize_chunk(chunk, query) for chunk in news_chunks]
        
        # 如果摘要总长度已经小于max_word，直接返回
        if sum(len(s) for s in summaries) <= max_word:
            return " ".join(summaries)
        
        # 否则，继续进行摘要，直到总长度不超过max_word
        while sum(len(s) for s in summaries) > max_word:
            if len(summaries) == 1:
                # 如果只剩一个摘要但仍然超过max_word，进行最后一次摘要
                final_prompt = f"请将以下摘要进一步压缩到不超过{max_word}个字：\n\n{summaries[0]}"
                return self.llm_client.one_chat(final_prompt)[:max_word]
            
            # 将现有的摘要分成两两一组进行进一步摘要
            new_summaries = []
            for i in range(0, len(summaries), 2):
                if i + 1 < len(summaries):
                    combined = summaries[i] + " " + summaries[i+1]
                    new_summary = summarize_chunk(combined, query)
                    new_summaries.append(new_summary)
                else:
                    new_summaries.append(summaries[i])
            
            summaries = new_summaries
        
        # 返回最终的摘要
        return " ".join(summaries)[:max_word]

    def extract_json_from_text(self, text: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        从文本中提取JSON对象并返回字典或字典列表。返回dict或者list

        :param text: 包含JSON数据的字符串。
        :return: 解析后的JSON对象（字典或字典列表）。
        :raises JSONDecodeError: 如果未能找到有效的JSON数据。
        """
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if not json_match:
            json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            json_match = re.search(r'\[[\s\S]*\]', text)
        
        if json_match:
            json_str = json_match.group(1) if '```json' in json_match.group() else json_match.group()
            return json.loads(json_str)
        
        raise json.JSONDecodeError("No valid JSON found in the text", text, 0)
    
    def get_self_description(self)->str:
        prompt="""
        适合用于选择股票范围的函数(只有get_code_name函数只返回名字和代码，其余函数均会返回数据，方便进行下一次筛选)：
            - select_stock_by_query                     使用最新行情数据，用自然语言进行筛选，返回值包含股票当前的数据信息
            - get_index_components                      输入指数代码，获得成分列表，返回值只有名字和代码
            - get_code_name                             全部股票代码的字典，返回值只有名字和代码
            - get_full_realtime_data                    获取全部股票目前的行情，返回Dict[Symnol,行情描述字符串]
            - get_concept_board_components              用自然语言进行概念板块选股，query只能针对板块的名字和板块的数据，返回值包含股票当前的数据信息
            - select_stocks_by_industry_board_query     用自然语言进行行业板块选股,query只能针对板块的名字和板块的数据，返回值包含股票当前的数据信息
            - get_rebound_stock_pool                    炸板股票池，返回值包含股票数据.返回Dict[Symbol,行情描述字符串]
            - get_new_stock_pool                        新股股票池，返回值包含股票数据.返回Dict[Symbol,行情描述字符串]
            - get_strong_stock_pool                     强势股票池，返回值包含股票数据.返回Dict[Symbol,行情描述字符串]
            - get_stock_comments_summary                千股千评数据.返回Dict[Symbol,行情描述字符串]。包括最新价、涨跌幅、换手率、市盈率、主力成本、机构参与度、综合得分、上升、目前排名、关注指数等数据
            - get_market_anomaly                        盘口异动，包括:'火箭发射', '快速反弹', '大笔买入', '封涨停板', '打开跌停板', '有大买盘', '竞价上涨', '高开5日线', '向上缺口', '60日新高', '60日大幅上涨', '加速下跌', '高台跳水', '大笔卖出', '封跌停板', '打开涨停板', '有大卖盘', '竞价下跌', '低开5日线', '向下缺口', '60日新低', '60日大幅下跌'
            - get_active_a_stock_stats                  活跃个股，查询周期：'近一月', '近三月', '近六月', '近一年'。，返回值包含股票数据
            - get_daily_lhb_details                     龙虎榜，返回值包含股票数据
            - get_institute_recommendations             机构推荐，包括：'最新投资评级', '上调评级股票', '下调评级股票', '股票综合评级', '首次评级股票', '目标涨幅排名', '机构关注度', '行业关注度', '投资评级选股'
            - get_investment_ratings                    最新投资评级
            - get_individual_stock_fund_flow_rank       资金流排名
            - select_by_stock_comments                  用自然语言查询千股千评论的数据，比如最受关注的10支股票，综合得分最高的10支股票
            - get_baidu_hotrank                         百度热门股票
            - get_baidu_recommendation                  百度推荐排名
            - get_baidu_sentiment_rank                  百度情绪指数排名
            - get_baidu_analysis_rank                   百度技术分析排名
            - get_top_holdings_by_market                持仓排名， "北向", "沪股通", "深股通"   "今日排行", "3日排行", "5日排行", "10日排行", "月排行", "季排行", "年排行" 
        用于获取市场整体信息的函数：
            - stock_market_desc                         市场平均市盈率等市场指标
            - get_current_buffett_index                 市场的巴菲特指数
        用于财报日期的函数
            - get_latest_financial_report_date           上一个财报日
            - get_next_financial_report_date             下一个财报日
        用于交易日期的函数
            - get_latest_trading_date                    九点半之前，返回今天之前的交易日，九点半之后返回包括今天在内的最近交易日
            - get_previous_trading_date                  永远返回不包含今天的交易日
        用于获取个股信息的函数
            - get_main_business_description              主营业务，返回包含主营业务信息的字符串
            - get_stock_info                             个股信息，返回个股指标字符串
            - get_stock_a_indicators                     个股指标,返回包含指标信息的字符串
            - get_baidu_analysis_summary                  百度个股分析，返回包含分析信息的字符串
            - get_stock_news                              个股新闻
            - get_news_updates                            获取某个时间以后的个股新闻
        用于代码查询的函数
            - search_index_code                         通过名称模糊查询指数代码
            - search_stock_code                         通过名称模糊查询股票代码
        用于查询财务数据
            - get_financial_analysis_summary            个股的财务分析指标
            - get_key_financial_indicators              关键财务指标
        用于查询财务数据细节(非必要勿使用)
            - get_balance_sheet_summary                 资产负债表摘要
            - get_profit_statement_summary              利润表摘要
            - get_cash_flow_statement_summary           现金流量表摘要
            - get_stock_balance_sheet_by_report_em      资产负债表完整数据
        用于查询行情摘要
            - summarize_historical_data                 股票历史数据摘要
            - summarize_historical_index_data           指数历史信息摘要
        用于查询行情细节(非必要勿使用)
            - get_historical_daily_data                 行情历史数据
            - get_index_data                           指数行情数据
        查询新闻数据
            - get_baidu_market_news                     百度市场新闻
            - get_baidu_stock_news                      百度个股新闻
            - get_market_news_300                       财联社新闻300条
        用于新闻数据处理
            - summarizer_news                           把新闻数据根据 query 的要求 总结出短摘要
        用于解析llm_client的json输出
            - extract_json_from_text                    从text中提取json,返回dict或者list
        
        """
        return prompt
    