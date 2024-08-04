
from datetime import datetime
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from qdrant_client import QdrantClient
from tqdm import tqdm
import tushare as ts

from ..embeddings._embedding import Embedding
from ..embeddings.embedding_factory import EmbeddingFactory

from ..utils.config_setting import Config
from ..utils.log import logger
from ..utils.tsdata import tsdata
from ..utils.timer import timer
from ..rag.qdrant_client_singleton import QdrantClientSingleton
import time
config = Config()

tushare_key =config.get("tushare_key")
ts.set_token(tushare_key)
import pandas as pd
import os
import pickle

db_path = "./database/embedding/tushare.db"
@timer
@tsdata
def get_stock_basic(limit=1000,offset=0)->pd.DataFrame:
    """
    获取股票列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.stock_basic( list_status='L', fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '股票'
    return data

@timer
@tsdata
def get_index_basic(limit=1000,offset=0)->pd.DataFrame:
    """
    获取指数列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.index_basic(fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '指数'
    return data
@timer
@tsdata
def get_fund_basic(limit=1000,offset=0)->pd.DataFrame:
    """
    获取基金列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fund_basic(fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '基金'
    return data
@timer
@tsdata
def get_fut_basic_CFFEX(limit=10000,offset=0)->pd.DataFrame:
    """
    获取期货列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fut_basic(exchange='CFFEX',fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期货'
    return data
@timer
@tsdata
def get_fut_basic_DCE(limit=10000,offset=0)->pd.DataFrame:
    """
    获取期货列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fut_basic(exchange='DCE',fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期货'
    return data
@timer
@tsdata
def get_fut_basic_CZCE(limit=10000,offset=0)->pd.DataFrame:
    """
    获取期货列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fut_basic(exchange='CZCE',fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期货'
    return data
@timer
@tsdata
def get_fut_basic_SHFE(limit=10000,offset=0)->pd.DataFrame:
    """
    获取期货列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fut_basic(exchange='SHFE',fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期货'
    return data
@timer
@tsdata
def get_fut_basic_INE(limit=10000,offset=0)->pd.DataFrame:
    """
    获取期货列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fut_basic(exchange='INE',fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期货'
    return data
@timer
@tsdata
def get_fut_basic_GFEX(limit=10000,offset=0)->pd.DataFrame:
    """
    获取期货列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fut_basic(exchange='GFEX',fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期货'
    return data
@timer
@tsdata
def get_opt_basic(limit=1000,offset=0)->pd.DataFrame:
    """
    获取期权列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.opt_basic(fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '期权'
    return data
@timer
@tsdata
def get_cb_basic(limit=2000,offset=0)->pd.DataFrame:
    """
    获取可转债列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.cb_basic(fields='ts_code,bond_full_name',limit=limit,offset=offset)
    data.rename(columns={'bond_full_name': 'name'}, inplace=True)
    data['type'] = '可转债'
    return data
@timer
@tsdata
def get_fx_obasic(limit=10000,offset=0)->pd.DataFrame:
    """
    获取外汇列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.fx_obasic(fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '外汇'
    return data
@timer
@tsdata
def get_hk_basic(limit=10000,offset=0)->pd.DataFrame:
    """
    获取港股列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.hk_basic(fields='ts_code,name',limit=limit,offset=offset)
    data['type'] = '港股'
    return data
@timer
@tsdata
def get_us_basic(limit=6000,offset=0)->pd.DataFrame:
    """
    获取美股列表
    :return:
    """
    pro = ts.pro_api()
    data = pro.us_basic(fields='ts_code,enname',limit=limit,offset=offset)
    data.rename(columns={'enname': 'name'}, inplace=True)
    data['type'] = '美股'
    time.sleep(6)
    return data

function_list=[get_stock_basic,get_index_basic,get_fund_basic,get_fut_basic_CFFEX,get_fut_basic_DCE,get_fut_basic_CZCE,get_fut_basic_SHFE,get_fut_basic_INE,get_fut_basic_GFEX,get_cb_basic,get_fx_obasic,get_hk_basic,get_us_basic]

def get_all_codes():
    results = []
    for func in function_list:
        print(f"{func.__name__} 正在获取数据")
        try:
            df = func()
            df.dropna(subset=['ts_code'],inplace=True)
            df.dropna(subset=['name'],inplace=True)
            results.append(df)
        except Exception as e:
            logger.error(f"获取{func.__name__}失败")
            logger.error(e)
    return pd.concat(results)

def build_tushare_db():
    from ..utils.config_setting import Config
    config = Config()
    if not config.has_key("tushare_key"):
        return
    today = datetime.now().strftime("%Y%m%d")
    cache_file = f"./output/tushare_code_{today}.pickle"
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            df = pickle.load(f)
    else:
        df = get_all_codes()
        with open(cache_file, "wb") as f:
            pickle.dump(df, f)
    #df = get_all_codes()

    df['content'] = df['ts_code']+','+df['name']+','+df['type']

    df = df.dropna(subset=['content'])

    embedding_factory = EmbeddingFactory()
    embedding: Embedding = embedding_factory.get_instance()
    # 批处理大小
    batch_size = 16
    embeddings = []
    # 计算总批次数
    total_batches = (len(df) + batch_size - 1) // batch_size

    # 使用tqdm创建进度条
    with tqdm(total=len(df), desc="处理嵌入") as pbar:
        # 分批转换为嵌入
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_embeddings = embedding.convert_to_embedding(batch['content'].tolist())
            embeddings.extend(batch_embeddings)
        
            # 更新进度条
            pbar.update(len(batch))
    
    client:QdrantClient = QdrantClientSingleton.get_instance(db_path)
    collection_name = 'ts_codes'
    # 删除已经存在的集合
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    dimensions = embedding.vector_size
    # 创建集合
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE)
    )
    
    points = []
    total = len(embeddings)

    for i, (embedding_vector, row) in enumerate(tqdm(zip(embeddings,  df.itertuples(index=False)), total=total, desc="存储数据")):
        points.append(
            PointStruct(
                id=i,
                vector=embedding_vector,
                payload={"ts_code": row.ts_code, "content":row.content}
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points
    )