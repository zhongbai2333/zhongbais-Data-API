import time
import fnmatch
from mcdreforged.api.all import *

from zhongbais_data_api.config import Config
from zhongbais_data_api.context import GlobalContext
from zhongbais_data_api.get_data import GetDat

_config, __mcdr_server = None, None
get_dat = GetDat()


def _is_bot_name(player: str, pattern: str) -> bool:
    """判断玩家名是否匹配机器人规则

    支持 shell 风格通配符: *, ?, []
    若 pattern 不包含上述通配符，则按“子串包含”判断，以保持与旧配置兼容。
    """
    if not pattern:
        return False
    # 统一转小写，进行不区分大小写的匹配
    name_l = player.lower()
    patt_l = pattern.lower()
    # 包含通配符时使用大小写无关的匹配
    if any(ch in patt_l for ch in "*?[]"):
        return fnmatch.fnmatchcase(name_l, patt_l)
    # 无通配符则退回到子串匹配（旧行为，大小写无关）
    return patt_l in name_l


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
    if player not in get_dat.player_list and not _is_bot_name(player, _config.bot_keyword):
        get_dat.player_list.append(player)


def on_player_left(_, player):
    if player in get_dat.player_list:
        get_dat.player_list.remove(player)
