import sys
import os
import shutil
import importlib.util

def check_exists():
    check_path = "../database/embedding"
    if os.path.exists(check_path):
        shutil.rmtree(check_path)

def lazy(fullname):
    import sys
    import importlib.util
    try:
        return sys.modules[fullname]
    except KeyError:
        spec = importlib.util.find_spec(fullname)
        module = importlib.util.module_from_spec(spec)
        loader = importlib.util.LazyLoader(spec.loader)
        # Make module with proper locking and get it inserted into sys.modules.
        loader.exec_module(module)
        return module

def rebuild_db():
    # 获取当前文件所在的目录
    current_file_directory = os.path.dirname(__file__)
    
    # 构建 ../core/rag/build_embedding_db.py 文件的完整路径
    target_file_path = os.path.join(current_file_directory, '..', 'core', 'rag', 'build_embedding_db.py')
    
    # 将 core 目录添加到 sys.path
    core_directory = os.path.join(current_file_directory, '..')
    sys.path.append(core_directory)
    
    # 加载目标文件作为模块
    target_module_name = 'build_embedding_db_module'
    spec = importlib.util.spec_from_file_location(target_module_name, target_file_path)
    built_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(built_module)
    
    # 从加载的模块中执行 build_akshare_embedding_db 函数
    built_module.build_akshare_embedding_db()

def download_embedding():
    current_file_directory = os.path.dirname(__file__)
    core_directory = os.path.join(current_file_directory, '..')
    sys.path.append(core_directory)

    module = lazy("core.embeddings.embedding_factory")
    factory = module.EmbeddingFactory()
    embedding = factory.get_instance()
    result = embedding.convert_to_embedding(["test"])
    print(result)
    print("Download embedding finished")
    module_reranker = lazy("core.embeddings.ranker_factory")
    factory_reranker = module_reranker.RankerFactory()
    reranker = factory_reranker.get_instance()
    result = reranker.rank("query",["test"])
    print(result)
    print("Download reranker finished")


if __name__ == "__main__":
    check_exists()
    rebuild_db()
    download_embedding()
