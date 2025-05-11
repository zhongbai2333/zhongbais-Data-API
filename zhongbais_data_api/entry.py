import time
from mcdreforged.api.all import *

from zhongbais_data_api.config import Config
from zhongbais_data_api.context import GlobalContext
from zhongbais_data_api.get_data import GetDat

_config, __mcdr_server = None, None
get_dat = GetDat()


def on_load(server: PluginServerInterface, prev):
    global _config, __mcdr_server, get_dat
    __mcdr_server = server
    _config = __mcdr_server.load_config_simple(target_class=Config)
    GlobalContext(__mcdr_server, _config)
    get_dat.init_mcdr()
    if prev is not None and hasattr(prev, "get_dat"):
        get_dat._player_info_callback = prev.get_dat._player_info_callback
        get_dat._player_list_callback = prev.get_dat._player_list_callback


def on_server_startup(_):
    get_dat.start()


# 插件卸载
def on_unload(_):
    get_dat.stop()
    if get_dat.wait_until_stopped(3):
        __mcdr_server.logger.info("Plugin Exit Finish!")
    else:
        __mcdr_server.logger.error("Plugin Exited but GetPos Service Can't Exit!")


# 在线玩家检测
def on_player_joined(_, player, __):
    if player not in get_dat.player_list and _config.bot_prefix not in player:
        get_dat.player_list.append(player)


def on_player_left(_, player):
    if player in get_dat.player_list:
        get_dat.player_list.remove(player)
