import time
import threading
import re
from mcdreforged.api.all import new_thread
from typing import Dict, Any, List, Tuple

from zhongbais_data_api.context import GlobalContext


class GetPos:
    POS_CMD = "execute as @a run data get entity @s Pos"
    DIM_CMD = "execute as @a run data get entity @s Dimension"

    def __init__(self):
        self._server = GlobalContext.get_mcdr()
        self._config = GlobalContext.get_config()
        self.player_info: Dict[str, Any] = {}
        self._stop_flag = threading.Event()

    def start(self) -> None:
        """
        循环检查 RCON 就绪，一旦就绪就开始定时抓取。
        建议在插件 apply 阶段或 on_enable 里调用此方法。
        """
        if self._stop_flag.is_set():
            return

        if self._server.is_rcon_running():
            # RCON 已就绪，启动调度
            self._schedule_next()
        else:
            # RCON 还没就绪，1秒后再试
            threading.Timer(1, self.start).start()

    def stop(self) -> None:
        """
        停止所有后续调度。
        """
        self._stop_flag.set()

    def _schedule_next(self) -> None:
        """
        在 refresh_pos_time 后执行一次 _fetch_positions。
        """
        if not self._stop_flag.is_set():
            interval = self._config.refresh_pos_time
            threading.Timer(interval, self._fetch_positions).start()

    @new_thread("GetPos")
    def getpos_player(self) -> None:
        """
        手动触发一次抓取（可选）。
        """
        self._fetch_positions()

    def _fetch_positions(self) -> None:
        """
        真正的抓取逻辑：获取位置、维度、解析并更新。
        最后再调度下一次。
        """
        try:
            pos_raw = self._rcon_execute(self.POS_CMD)
            dim_raw = self._rcon_execute(self.DIM_CMD)
            if pos_raw and dim_raw:
                self._process_results(pos_raw, dim_raw)
        except Exception as e:
            self._server.logger.error(f"[GetPos] Call failed: {e}")
        finally:
            # 不论成功或失败，都调度下一次
            self._schedule_next()

    # —— 以下方法与之前类似，不再重复 —— #
    def _process_results(self, pos_raw: str, dim_raw: str) -> None:
        pos_lines = [l for l in pos_raw.splitlines() if l.strip()]
        dim_lines = [l for l in dim_raw.splitlines() if l.strip()]
        for pos_line, dim_line in zip(pos_lines, dim_lines):
            name, coords = self._parse_position_info(pos_line)
            dimension = self._parse_dimension_info(dim_line)
            coords_int = [int(float(c)) for c in coords]
            self._update_player(name, coords_int, dimension)
        online = {line.split()[0] for line in pos_lines}
        for name in set(self.player_info) - online:
            del self.player_info[name]

    @staticmethod
    def _parse_position_info(line: str) -> Tuple[str, List[str]]:
        name = line.split()[0]
        coords_str = line.split("Pos:")[-1]
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", coords_str)
        return name, coords

    @staticmethod
    def _parse_dimension_info(line: str) -> str:
        line = line.split('"')
        return line[1]

    def _update_player(self, name: str, coords: List[int], dimension: str) -> None:
        now = int(time.time())
        data = self.player_info.get(
            name,
            {
                "position": None,
                "dimension": None,
                "last_update": now,
                "is_afk": False,
            },
        )
        if data["position"] == coords:
            if (
                now - data["last_update"] >= self._config.afk_time
                and not data["is_afk"]
            ):
                data["is_afk"] = True
        else:
            data.update(
                {
                    "position": coords,
                    "dimension": dimension,
                    "last_update": now,
                    "is_afk": False,
                }
            )
        self.player_info[name] = data
        if self._config.debug:
            self._server.logger.info(f"[DEBUG] PlayerInfo: \n{self.player_info}")

    def _rcon_execute(self, cmd: str) -> str:
        if self._server.is_rcon_running():
            return self._server.rcon_query(cmd) or ""
        else:
            if not self._stop_flag.is_set():
                self._server.logger.error("[GetPos] Need RCON Support!")
                self.stop()
            return ""
