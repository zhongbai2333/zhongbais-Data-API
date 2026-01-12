import threading
import re
import json
import fnmatch
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
        self._server_started = False  # 仅在 on_server_startup 后置为 True，用于拦截过早的手动刷新

        self.player_list: List[str] = []
        self._player_list_callbacks: List[PlayerListCallback] = []
        self._player_info_callbacks: List[Tuple[List[str], PlayerInfoCallback]] = []

    def _is_bot_name(self, name: str) -> bool:
        """根据配置判断是否为机器人名（不区分大小写，支持通配符）"""
        pattern = getattr(self._config, "bot_keyword", "") or ""
        if not pattern:
            return False
        name_l = name.lower()
        patt_l = pattern.lower()
        if any(ch in patt_l for ch in "*?[]"):
            return fnmatch.fnmatchcase(name_l, patt_l)
        return patt_l in name_l

    def init_mcdr(self) -> None:
        """初始化 MCDR 相关引用"""
        self._server = GlobalContext.get_mcdr()
        self._config = GlobalContext.get_config()

    def start(self) -> None:
        # on_server_startup 调用时标记服务已启动
        self._server_started = True
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
        # 在服务器未启动或 RCON 未就绪时忽略手动刷新
        if not self._server_started or not self._server or not self._server.is_rcon_running():
            try:
                if getattr(self._config, "debug", False):
                    self._server.logger.info(f"[GetDat] server_started：{self._server_started} server: { self._server} server.is_rcon_running: { self._server.is_rcon_running()}")
                self._server.logger.info("[GetDat] manual_fetch ignored: server not started or RCON not ready")
            except Exception:
                pass
            return
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

            # 1. 分发每位玩家的数据（过滤机器人）
            debug_samples = []
            filtered_matches = []
            for m in matches:
                name = m.group("name").strip()
                if self._is_bot_name(name):
                    continue
                filtered_matches.append(m)
                raw_nbt = m.group("data")
                json_str: Optional[str] = None
                try:
                    json_str = self._nbt_to_json(raw_nbt)
                    if json_str.count("{") != json_str.count("}"):
                        self._server.logger.error(f"[GetDat] json_str括号未闭合{'{'}数量{json_str.count('{')} ,{'}'}数量{json_str.count('}')}")
                    data: Dict[str, Any] = json.loads(json_str)
                    self._dispatch_player_info(name, data)
                    # 收集少量基础信息用于调试
                    if getattr(self._config, "debug", False) and len(debug_samples) < 3:
                        debug_samples.append({
                            "name": name,
                            "Pos": data.get("Pos"),
                            "Dimension": data.get("Dimension"),
                            "Rotation": data.get("Rotation"),
                        })
                except Exception as pe:
                    # 单玩家解析失败不影响其他玩家
                    self._server.logger.error(
                        f"[GetDat] JSON parse failed for {name}: {pe}"
                    )
                    if getattr(self._config, "debug", False):
                        try:
                            err_col = getattr(pe, 'colno', None)
                            if err_col is None:
                                err_col = max(0, len(json_str) // 2)
                            err_col = min(err_col, len(json_str) - 1) if json_str else 0
                            start = max(0, err_col - 50)
                            end = min(len(json_str), err_col + 50)
                            context = json_str[start:end]
                            self._server.logger.error(
                                f"[GetDat] Error position (col {err_col}): ...{context}..."
                            )
                        except Exception:
                            pass
                        snippet_src = (raw_nbt or "")[:300]
                        snippet_json = (json_str or "")[:300]
                        self._server.logger.info(
                            f"[GetDat][debug] SNBT snippet for {name}: {snippet_src}"
                        )
                        self._server.logger.info(
                            f"[GetDat][debug] JSON  snippet for {name}: {snippet_json}"
                        )
                    continue

            # 2. 在线/离线玩家列表变化
            # 从 Match 对象里取 name
            online = [m.group("name").strip() for m in filtered_matches]

            # Debug: 输出本轮被获取到数据的玩家列表
            try:
                if getattr(self._config, "debug", False):
                    self._server.logger.info(f"[GetDat][debug] fetched players: {online}")
                    if debug_samples:
                        self._server.logger.info(f"[GetDat][debug] basic info samples: {debug_samples}")
            except Exception:
                # debug 日志不可影响主流程
                pass

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
        """NBT→合法 JSON 的转换（轻量处理，不保证覆盖全部 SNBT 细节）"""
        s = nbt
        # 1) [B;…]/[I;…]/[L;…] → […], 去掉类型前缀
        s = re.sub(r"\[(?:B|I|L);(.*?)\]", r"[\1]", s, flags=re.DOTALL)
        # 2) 仅对真正的键名加双引号
        s = re.sub(r"(?<=[\{\[,])\s*([A-Za-z0-9_]+)\s*:", r'"\1":', s)
        # 3) 去掉浮点后缀 dDfF（兼容科学计数法，如 6.0E7d / 1e-3f）
        s = re.sub(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*[dDfF]", r"\1", s)
        # 4) 去掉整数/字节/短整型/长整型后缀 bBsSlL
        s = re.sub(r"(-?\d+)\s*[bBsSlL]", r"\1", s)
        # 5) 处理省略号 <...> 为合法空列表 []
        s = re.sub(r'<\.\.\.>', r'""', s)
        # # 6) 处理字符串引号：重点修复内层双引号的转义
        # # 单引号包裹的字符串（如 'abc"def' → "abc\"def"）
        # s = re.sub(r"'(.*?)'", 
        #     lambda m: '"' + m.group(1).replace('"', r'\"').replace('\\', r'\\') + '"', 
        #     s, 
        #     flags=re.DOTALL
        # )
        def escape_str(match):
            raw_str = match.group(1)  # 获取单引号内的原始字符串
            return json.dumps(raw_str)  # 自动处理双引号、反斜杠等转义
        s = re.sub(r"'(.*?)'", escape_str, s, flags=re.DOTALL)
        return s
