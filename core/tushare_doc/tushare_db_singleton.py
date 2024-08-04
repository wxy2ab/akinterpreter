from qdrant_client import QdrantClient


class TushareDBSingleton:
    _instances = {}

    @classmethod
    def get_instance(cls, db_path):
        if db_path not in cls._instances:
            cls._instances[db_path] = QdrantClient(path=db_path)
        return cls._instances[db_path]