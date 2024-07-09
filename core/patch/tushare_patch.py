import tushare as ts
from ..utils.config_setting import Config
import akshare as ak
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton

def pro_api_patch():
    config = Config()
    if config.has_key('tushare_key'):
        token = config.get('tushare_key')
        ts.set_token(token)
        single = AKShareDataSingleton()
        single.classified_functions["新闻数据"].append("pro.news: 获取主流新闻网站的快讯新闻数据")
        single.akshare_docs["pro.news"]="""
接口：news
描述：获取主流新闻网站的快讯新闻数据
限量：单次最大1000条新闻
输入参数

名称	类型	必选	描述
start_date	datetime	Y	开始日期
end_date	datetime	Y	结束日期
src	str	Y	新闻来源 见下表

数据源

来源名称	src标识	描述
新浪财经	sina	获取新浪财经实时资讯
同花顺	10jqka	同花顺财经新闻
东方财富	eastmoney	东方财富财经新闻
云财经	yuncaijing	云财经新闻

日期输入说明：
如果是加时间参数，可以设置：start_date='2018-11-20 09:00:00', end_date='2018-11-20 22:05:03'

输出参数

名称	类型	默认显示	描述
datetime	str	Y	新闻时间
content	str	Y	内容
title	str	Y	标题
channels	str	N	分类

接口调用:
import tushare as ts
pro = ts.pro_api()

df = pro.news(src='sina', start_date='2018-11-21 09:00:00', end_date='2018-11-22 10:10:00')
"""


