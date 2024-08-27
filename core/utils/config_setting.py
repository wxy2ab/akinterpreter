import os
import configparser

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=Singleton):
    def __init__(self, path="setting.ini"):
        self.file_name = path
        self.config = configparser.ConfigParser()
        
        if os.path.exists(path):
            self.config.read(path, encoding='utf-8')
            self.use_file = True
        else:
            self.use_file = False

    def get(self, key: str = "token", /, section: str = "Default"):
        value = None
        if self.use_file:
            if self.config.has_section(section):
                value = self.config[section].get(key)
        
        # 如果在文件中没有找到值，或者不使用文件，尝试从环境变量获取
        if value is None:
            value = os.environ.get(key.upper())
        
        return value

    def has_key(self, key: str = "token", /, section: str = "Default"):
        if self.use_file:
            if self.config.has_section(section):
                if key in self.config[section]:
                    return True
        
        # 如果在文件中没有找到，或者不使用文件，检查环境变量
        return key.upper() in os.environ

    def set(self, key: str = "token", value: str = "", /, section: str = "Default"):
        if self.use_file:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config[section][key] = value
            with open(self.file_name, "w") as configfile:
                self.config.write(configfile)
        else:
            # 注意：在非文件模式下，set 方法不会实际修改环境变量
            print(f"Warning: Cannot set {key} = {value} in environment variable mode")