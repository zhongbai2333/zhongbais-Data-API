from mcdreforged.api.all import PluginServerInterface
from zhongbais_data_api.config import Config

__mcdr_server: PluginServerInterface = None
_config: Config = None

class GlobalContext(object):
    def __init__(self, mcdr_interface: PluginServerInterface, config: Config):
        global __mcdr_server, _config
        __mcdr_server = mcdr_interface
        _config = config
    
    @staticmethod
    def get_mcdr() -> PluginServerInterface:
        return __mcdr_server
    
    @staticmethod
    def get_config() -> Config:
        return _config

