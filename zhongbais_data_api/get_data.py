import threading
import re
import json
from typing import Any, Dict, List, Callable, Tuple, Optional
from mcdreforged.api.all import new_thread
from zhongbais_data_api.context import GlobalContext

# 回调类型别名
PlayerListCallback = Callable[[str, List[str]], None]
PlayerInfoCallback = Callable[[str, Dict[str, Any]], None]


class GetDat:
    DAT_CMD = "execute as @a run data get entity @s"
    # 正则：从行首匹配 “Name has the following entity data: {...}”
    _dat_pattern = re.compile(
        r"(?P<name>.+?)\s+has the following entity data:\s*"
        r"(?P<data>\{.*?\})"
        r"(?=(?:\s*\w+\s+has the following entity data:)|\s*$)",
        re.DOTALL,
    )

    def __init__(self):
        self._server = None
        self._config = None
        self._timer: Optional[threading.Timer] = None
        self._stop_flag = threading.Event()
        self._stopped_event = threading.Event()

        self.player_list: List[str] = []
        self._player_list_callbacks: List[PlayerListCallback] = []
        self._player_info_callbacks: List[Tuple[List[str], PlayerInfoCallback]] = []

    def init_mcdr(self) -> None:
        """初始化 MCDR 相关引用"""
        self._server = GlobalContext.get_mcdr()
        self._config = GlobalContext.get_config()

    def start(self) -> None:
        if self._stop_flag.is_set():
            return

        if self._server.is_rcon_running():
            self._schedule_next()
        else:
            t = threading.Timer(1, self.start)
            t.daemon = True
            t.name = f"{self.__class__.__name__}-Starter"
            t.start()

    def stop(self) -> None:
        """停止所有后续调度"""
        self._stop_flag.set()
        if self._timer:
            self._timer.cancel()
        self._stopped_event.set()

    def wait_until_stopped(self, timeout: float = None) -> bool:
        """阻塞直到抓取循环完全停止"""
        return self._stopped_event.wait(timeout)

    def register_player_list_callback(self, cb: PlayerListCallback) -> None:
        """在线玩家列表变化时回调"""
        self._player_list_callbacks.append(cb)

    def register_player_info_callback(
        self, nbt_keys: Optional[List[str]], cb: PlayerInfoCallback
    ) -> None:
        """
        注册玩家数据回调：
        - nbt_keys 为空列表或 None 时，回调接收所有字段
        - 否则只返回 nbt_keys 指定的字段
        """
        keys = nbt_keys or []
        self._player_info_callbacks.append((keys, cb))

    @new_thread("GetDat-ManualFetch")
    def manual_fetch(self) -> None:
        """外部手动触发一次抓取"""
        self._fetch_datas()

    def _schedule_next(self) -> None:
        if self._stop_flag.is_set():
            return
        interval = self._config.refresh_data_time
        t = threading.Timer(interval, self._fetch_datas)
        t.daemon = True
        t.name = f"{self.__class__.__name__}-Fetcher"
        self._timer = t
        t.start()

    def _fetch_datas(self) -> None:
        try:
            raw = self._rcon_execute(self.DAT_CMD) or ""
            matches = list(self._dat_pattern.finditer(raw))

            # 1. 分发每位玩家的数据
            for m in matches:
                name = m.group("name").strip()
                raw_nbt = m.group("data")
                json_str = self._nbt_to_json(raw_nbt)
                data: Dict[str, Any] = json.loads(json_str)
                self._dispatch_player_info(name, data)

            # 2. 在线/离线玩家列表变化
            # 从 Match 对象里取 name
            online = [m.group("name").strip() for m in matches]

            added = set(online) - set(self.player_list)
            removed = set(self.player_list) - set(online)

            # 更新 self.player_list
            for name in added:
                self.player_list.append(name)
            for name in removed:
                self.player_list.remove(name)

            # 回调通知列表变动
            for cb in self._player_list_callbacks:
                for name in added | removed:
                    cb(name, list(self.player_list))

        except Exception as e:
            self._server.logger.error(f"[GetDat] Call failed: {e}")
        finally:
            self._schedule_next()
            if self._stop_flag.is_set():
                self._stopped_event.set()

    def _dispatch_player_info(self, name: str, data: Dict[str, Any]) -> None:
        """根据注册时指定的字段回调玩家信息"""
        for keys, cb in self._player_info_callbacks:
            if not keys:
                # 全字段
                cb(name, data)
            else:
                # 按需过滤
                subset = {k: data.get(k) for k in keys}
                cb(name, subset)

    def _rcon_execute(self, cmd: str) -> str:
        if self._server.is_rcon_running():
            return self._server.rcon_query(cmd) or ""
        else:
            if not self._stop_flag.is_set():
                self._server.logger.error("[GetPos] Need RCON Support!")
                self.stop()
            return ""

    @staticmethod
    def _nbt_to_json(nbt: str) -> str:
        """NBT→合法 JSON 的转换（保留原注释）"""
        s = nbt
        # 1) [I;…] → […], 去掉 I;
        s = re.sub(r"\[I;(.*?)\]", r"[\1]", s)
        # 2) 仅对真正的键名加双引号
        s = re.sub(r"(?<=[\{\[,])\s*([A-Za-z0-9_]+)\s*:", r'"\1":', s)
        # 3) 去掉浮点后缀 dDfF
        s = re.sub(r"(-?\d+\.\d+)\s*[dDfF]", r"\1", s)
        # 4) 去掉整数/字节/秒后缀 bBsS
        s = re.sub(r"(-?\d+)\s*[bBsS]", r"\1", s)
        return s
