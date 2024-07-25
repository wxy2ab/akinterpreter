import os
from core.akshare_doc.akshare_tool_info import AkshareToolInfo
from core.embeddings._embedding import Embedding
from core.embeddings.embedding_factory import EmbeddingFactory
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance

def build_embedding_db():
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

    # 过滤包含 'http' 的文档首行
    filtered_funcs = [f for f in funcs if 'http' not in f['docstring'].splitlines()[0]]

    # 准备数据
    names = [f['name'] for f in filtered_funcs]
    contents = [f"{f['name']}: {f['docstring'].splitlines()[0]}" for f in filtered_funcs]

    # 批处理大小
    batch_size = 16
    embeddings = []

    # 分批转换为嵌入
    for i in range(0, len(contents), batch_size):
        batch = contents[i:i+batch_size]
        batch_embeddings = embedding.convert_to_embedding(batch)
        embeddings.extend(batch_embeddings)

    # 连接到 QdrantDB
    client = QdrantClient(path=db_path)

    # 确保集合存在
    collection_name = 'akshare_embeddings'
        # 创建或重新创建集合
    if client.collection_exists('akshare_embeddings'):
        client.delete_collection('akshare_embeddings')

    client.create_collection(
    collection_name='akshare_embeddings',
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

    points = [
    PointStruct(
        id=i,
        vector=embedding,  # 直接使用向量，不需要命名
        payload={"name": name, "content": content}
    )
    for i, (embedding, name, content) in enumerate(zip(embeddings, names, contents))
]

    client.upsert(
        collection_name='akshare_embeddings',
        points=points
    )

    print(f"Successfully stored {len(points)} embeddings in {db_path}")

# 示例使用
if __name__ == "__main__":
    build_embedding_db()
