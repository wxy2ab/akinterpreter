import os
import re

from tqdm import tqdm
from core.akshare_doc.akshare_tool_info import AkshareToolInfo
from core.embeddings._embedding import Embedding
from core.embeddings.embedding_factory import EmbeddingFactory
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
import time

def build_akshare_embedding_db():
    # 创建目录和文件路径
    db_directory = './database/embedding'
    db_path = os.path.join(db_directory, 'akshare.db')
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    # 初始化 AkshareToolInfo 并提取函数
    info = AkshareToolInfo()
    funcs = info.extract_akshare_functions()

    # 初始化 EmbeddingFactory 并获取 Embedding 实例
    embedding_factory = EmbeddingFactory()
    embedding: Embedding = embedding_factory.get_instance()
    if hasattr(embedding, 'emb_type'):
        embedding.emb_type = 'db'

    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'  
    # 过滤包含 'http' 的文档首行
    filtered_funcs = [ {"name":f['name'],"docstring":re.sub(url_pattern, '', f['docstring'])}  for f in funcs]
    filtered_funcs = [ {"name":f['name'],"docstring":re.sub(r'股本股东-|经济数据-|经济数据一览-|经济数据-|申万指数-|指数发布-|市场数据-|基金产品公示-|诚信信息公示-|信息公示-|概念板-|数据中心-|特色数据-|行情中心-|\n', '', f['docstring'])}  for f in filtered_funcs]

    # 准备数据
    names = [f['name'] for f in filtered_funcs]
    contents = [f"{f['name']}: {f['docstring'].split(":rtype")[0]}" for f in filtered_funcs]

    # 批处理大小
    batch_size = 16
    embeddings = []

    # 计算总批次数
    total_batches = (len(contents) + batch_size - 1) // batch_size

    # 使用tqdm创建进度条
    with tqdm(total=len(contents), desc="处理嵌入") as pbar:
        # 分批转换为嵌入
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i+batch_size]
            batch_embeddings = embedding.convert_to_embedding(batch)
            embeddings.extend(batch_embeddings)

            # 更新进度条
            pbar.update(len(batch))

    # 连接到 QdrantDB
    client = QdrantClient(path=db_path)

    # 确保集合存在
    collection_name = 'akshare_embeddings'
        # 创建或重新创建集合
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    
    dimensions = embedding.vector_size

    client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE)
)

    points = []
    total = len(embeddings)  # 假设embeddings、names和contents长度相同

    for i, (embedding, name, content) in enumerate(tqdm(zip(embeddings, names, contents), total=total, desc="存储数据")):
        points.append(
            PointStruct(
                id=i,
                vector=embedding,
                payload={"name": name, "content": content}
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points
    )

    print(f"Successfully stored {len(points)} embeddings in {db_path}")

# 示例使用
if __name__ == "__main__":
    build_akshare_embedding_db()
