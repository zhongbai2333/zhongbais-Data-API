# zhongbais Data API

一个基于 MCDReforged 的玩家位置信息获取与回调 API，封装了定时拉取、AFK 检测等功能，方便其他插件或脚本统一访问和订阅玩家位置、维度、朝向等数据变化。

[English](README.md) | 简中

---

## 特性

- **定时拉取**：自动按配置的间隔定时通过 RCON 获取所有在线玩家的 Pos/Dim/Rot 数据
- **AFK 检测**：根据配置的 AFK 超时时间，自动标记玩家是否进入 AFK 状态  
- **回调机制**：基于 `ObservableDict`，自动触发回调，方便业务层实时处理数据变化  

---

## 快速上手

```python
from mcdreforged.api.all import PluginServerInterface, new_thread
from zhongbais_data_api import zbDataAPI

def on_load(self, server: PluginServerInterface, old):
    # 注册回调：当玩家信息更新时打印
    zbDataAPI.register_player_info_callback(self.on_player_update)

def on_player_update(self, name: str, info: dict):
    """
    name: 玩家名
    info: {
        "position": [x, y, z],
        "rotation": [yaw, pitch],
        "dimension": "minecraft:overworld",
        "last_update_time":  时间戳,
        "is_afk": 是否 AFK
    }
    """
    self.server.logger.info(f"[PlayerUpdate] {name} -> {info}")
```

---

## API 文档

### `zbDataAPI.get_player_info() -> dict`

返回当前所有在线玩家的信息字典，结构为：

```python
{
  "Alice": {
    "position": [x, y, z],
    "rotation": [yaw, pitch],
    "dimension": "minecraft:overworld",
    "last_update_time":  时间戳,
    "is_afk": False,
  },
  "Bob": { … },
  …
}
```

### `zbDataAPI.get_player_list() -> list`

返回当前所有在线玩家的名字列表：

```python
["Alice", "Bob", …]
```

### `zbDataAPI.register_player_info_callback(func)`

注册一个回调函数 `func(player_info: dict)`，当任意玩家的 **完整信息**（Pos/Rot/Dim/AFK）变化时触发。

- **参数**

  - `func(player_info)`：`player_info` 为最新的玩家数据字典。

### `zbDataAPI.register_player_list_callback(func)`

注册一个回调函数 `func(player_list: list)`，当在线玩家 **增减** 时触发。

- **参数**

  - `func(player_list)`：`player_list` 为最新的玩家名列表。

### `zbDataAPI.refresh_getpos() -> None`

手动触发一次拉取，等同于调用内部的 `get_pos.getpos_player()`。

---

## 开发与贡献

1. Fork 本仓库
2. 新建分支 `feature/xxx`
3. 提交你的改动并发 Pull Request

欢迎提交 issue 和 PR，让这个 API 更加完善！

---

## 许可协议

本项目遵循 GPLv3 许可，详情见 [LICENSE](./LICENSE) 文件。
