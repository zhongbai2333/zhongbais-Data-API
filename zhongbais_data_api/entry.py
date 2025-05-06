import time
from mcdreforged.api.all import *

from zhongbais_data_api.config import Config
from zhongbais_data_api.context import GlobalContext
from zhongbais_data_api.get_pos import GetPos

_config, __mcdr_server = None, None
get_pos = GetPos()


def on_load(server: PluginServerInterface, prev):
    global _config, __mcdr_server, get_pos
    __mcdr_server = server
    _config = __mcdr_server.load_config_simple(target_class=Config)
    GlobalContext(__mcdr_server, _config)
    get_pos.init_mcdr()
    if prev is not None:
        get_pos.player_info = prev.get_pos.player_info
        get_pos.start()


def on_server_startup(_):
    get_pos.start()


# 插件卸载
def on_unload(_):
    get_pos.stop()
    if get_pos.wait_until_stopped(3):
        __mcdr_server.logger.info("Plugin Exit Finish!")
    else:
        __mcdr_server.logger.error("Plugin Exited but GetPos Service Can't Exit!")


# 在线玩家检测
def on_player_joined(_, player, __):
    if player not in get_pos.player_info.keys() and _config.bot_prefix not in player:
        get_pos.player_info[player] = {
            "position": None,
            "rotation": None,
            "dimension": None,
            "last_update_time": int(time.time()),
            "is_afk": False,
        }


def on_player_left(_, player):
    if player in get_pos.player_info.keys():
        del get_pos.player_info[player]
