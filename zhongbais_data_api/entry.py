import time
from mcdreforged.api.all import *

from zhongbais_data_api.config import Config
from zhongbais_data_api.context import GlobalContext
from zhongbais_data_api.get_pos import GetPos

_config, __mcdr_server, get_pos = None, None, None


def get_player_info() -> dict:
    """
    获取玩家信息字典

    Returns:
        dict: 玩家信息
    """
    return get_pos.player_info


def get_player_list() -> list:
    """
    获取在线玩家列表

    Returns:
        list: 玩家列表
    """
    return list(get_pos.player_info.keys())


def on_load(server: PluginServerInterface, prev):
    global _config, __mcdr_server, get_pos
    __mcdr_server = server
    _config = __mcdr_server.load_config_simple(target_class=Config)
    GlobalContext(__mcdr_server, _config)
    get_pos = GetPos()
    if prev is not None:
        get_pos.player_info = prev.get_pos.player_info
        get_pos.start()


def on_server_startup(_):
    get_pos.start()


# 插件卸载
def on_unload(_):
    get_pos.stop()


# 在线玩家检测
def on_player_joined(_, player, __):
    if player not in get_pos.player_info.keys() and _config.bot_prefix not in player:
        get_pos.player_info[player] = {
            "position": None,
            "dimension": None,
            "last_update_time": int(time.time()),
            "is_afk": False,
        }


def on_player_left(_, player):
    if player in get_pos.player_info.keys():
        del get_pos.player_info[player]
