from qdrant_client import QdrantClient


class QdrantClientSingleton:
    _instances = {}

    @classmethod
    def get_instance(cls, db_path)->QdrantClient:
        if db_path not in cls._instances:
            cls._instances[db_path] = QdrantClient(path=db_path)
        return cls._instances[db_path]