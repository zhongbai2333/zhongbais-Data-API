import time
import threading
import re
from mcdreforged.api.all import new_thread
from typing import List

from zhongbais_data_api.context import GlobalContext
from zhongbais_data_api.tools import ObservableDict


class GetPos:
    POS_CMD = "execute as @a run data get entity @s Pos"
    DIM_CMD = "execute as @a run data get entity @s Dimension"
    ROT_CMD = "execute as @a run data get entity @s Rotation"

    def __init__(self):
        self._timer: threading.Timer = None
        self._stopped_event = threading.Event()
        self.player_info: ObservableDict = ObservableDict()
        self._stop_flag = threading.Event()

        # 预编译正则，用于处理粘连输出
        self._pos_pattern = re.compile(
            r"([^\s]+) has the following entity data: \[([^\]]+)\]"
        )
        self._dim_pattern = re.compile(
            r'([^\s]+) has the following entity data: "([^"]+)"'
        )
        self._rot_pattern = re.compile(
            r"([^\s]+) has the following entity data: \[([^\]]+)\]"
        )

    def init_mcdr(self) -> None:
        """初始化 MCDR 相关变量"""
        self._server = GlobalContext.get_mcdr()
        self._config = GlobalContext.get_config()

    def start(self) -> None:
        if self._stop_flag.is_set():
            return
        if self._server.is_rcon_running():
            self._schedule_next()
        else:
            timer = threading.Timer(1, self.start)
            timer.name = f"{self.__class__.__name__}-Starter"
            timer.daemon = True
            timer.start()

    def stop(self) -> None:
        """停止所有后续调度"""
        self._stop_flag.set()
        if self._timer:
            self._timer.cancel()
        self._stopped_event.set()

    def wait_until_stopped(self, timeout: float = None) -> bool:
        """阻塞直到循环彻底停止，返回是否在 timeout 秒内完成"""
        return self._stopped_event.wait(timeout)

    def _schedule_next(self) -> None:
        if self._stop_flag.is_set():
            return
        interval = self._config.refresh_pos_time
        timer = threading.Timer(interval, self._fetch_positions)
        timer.name = f"{self.__class__.__name__}-Fetcher"
        timer.daemon = True
        self._timer = timer
        timer.start()

    @new_thread("GetPos-ManualFetch")
    def getpos_player(self) -> None:
        self._fetch_positions()

    def _fetch_positions(self) -> None:
        """抓取逻辑：正则拆分多玩家粘连输出，分别更新位置、维度、旋转。"""
        try:
            pos_raw = self._rcon_execute(self.POS_CMD)
            dim_raw = self._rcon_execute(self.DIM_CMD)
            rot_raw = self._rcon_execute(self.ROT_CMD)

            now = int(time.time())
            # 提取所有玩家的位置数据
            pos_matches = self._pos_pattern.findall(pos_raw)
            # 提取维度和旋转数据到字典
            dim_dict = dict(self._dim_pattern.findall(dim_raw))
            rot_dict = dict(self._rot_pattern.findall(rot_raw))

            for name, coords_str in pos_matches:
                coords = [float(x.rstrip("df")) for x in coords_str.split(",")]
                dimension = dim_dict.get(name, "")
                rot_str = rot_dict.get(name, "")
                rot_coords = (
                    [float(x.rstrip("df")) for x in rot_str.split(",")]
                    if rot_str
                    else []
                )

                self._update_player(name, coords, dimension, rot_coords, now)

            # 清理离线玩家
            online = {name for name, _ in pos_matches}
            for name in set(self.player_info) - online:
                del self.player_info[name]

        except Exception as e:
            self._server.logger.error(f"[GetPos] Call failed: {e}")
        finally:
            self._schedule_next()
            if self._stop_flag.is_set():
                self._stopped_event.set()

    def _update_player(
        self,
        name: str,
        coords: List[float],
        dimension: str,
        rot_coords: List[float],
        now: int,
    ) -> None:
        old = self.player_info.get(
            name,
            {
                "position": None,
                "rotation": None,
                "dimension": None,
                "last_update_time": now,
                "is_afk": False,
            },
        )
        changed = (
            old["position"] != coords
            or old["dimension"] != dimension
            or old["rotation"] != rot_coords
        )
        if changed:
            new_data = {
                "position": coords,
                "rotation": rot_coords,
                "dimension": dimension,
                "last_update_time": now,
                "is_afk": False,
            }
            self.player_info[name] = new_data
        else:
            if (
                now - old["last_update_time"] >= self._config.afk_time
                and not old["is_afk"]
            ):
                old["is_afk"] = True
                old["last_update_time"] = now
                self.player_info[name] = old.copy()

    def _rcon_execute(self, cmd: str) -> str:
        if self._server.is_rcon_running():
            return self._server.rcon_query(cmd) or ""
        else:
            if not self._stop_flag.is_set():
                self._server.logger.error("[GetPos] Need RCON Support!")
                self.stop()
            return ""
