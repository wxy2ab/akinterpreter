import configparser
try:
    from  .single_ton  import  Singleton
except:
    from single_ton import Singleton
import os


class Config(metaclass = Singleton):
    def __init__(self, path="setting.ini"):
        self.file_name = path
        if not os.path.exists(path):
            with open(path, "w") as file:
                pass
        self.config = configparser.ConfigParser()
        self.config.read(path)
        
    def get(self,  key:str="token" ,/, section:str="Default"):
        if not self.config.has_section(section):
            self.config.add_section(section)
        return self.config[section][key]

    def has_key(self, key:str="token" ,/, section:str="Default"):
        if not self.config.has_section(section):
            self.config.add_section(section)
        return key in self.config[section]

    def set(self, key:str="token", value="" ,/, section:str="Default"):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config[section][key] = value
        with open(self.file_name, "w") as configfile:
            self.config.write(configfile)