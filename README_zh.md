# zhongbais Data API

一个基于 MCDReforged 的玩家位置信息获取与回调 API，封装了定时拉取等功能，方便其他插件或脚本统一访问和订阅玩家位置、维度、朝向等数据变化。

[English](README.md) | 简中

---

## 特性

- **定时拉取**：自动按配置的间隔通过 RCON 获取所有在线玩家的 NBT 数据  
- **回调机制**：封装了回调列表，支持按需订阅玩家信息变化或在线列表增减  

---

## 快速上手

```python
from mcdreforged.api.all import PluginServerInterface, new_thread
from zhongbais_data_api import zbDataAPI

def on_load(self, server: PluginServerInterface, old):
    # 监听所有NBT的信息变化
    zbDataAPI.register_player_info_callback(self.on_player_update)
    # 也可以只监听部分NBT的信息变化
    # zbDataAPI.register_player_info_callback(self.on_player_update, ['Pos', 'Dimension', ...])

    # 监听在线玩家列表变化
    zbDataAPI.register_player_list_callback(self.on_player_list_change)

def on_player_update(self, name: str, info: dict):
    """
    name: 玩家名
    info: {
      "Pos": [...],         # 位置 [x, y, z]
      "Rotation": [...],    # 朝向 [yaw, pitch]
      "Dimension": "...",   # 维度
      …                     # 可根据配置添加其他字段
    }
    """
    self.server.logger.info(f"[PlayerUpdate] {name} -> {info}")

def on_player_list_change(self, player: str, current_list: list):
    # player: 新增或离线的玩家名
    # current_list: 当前所有在线玩家列表
    self.server.logger.info(f"[PlayerList] {player} changed, now: {current_list}")

# 在需要时手动触发一次拉取（例如测试时）
zbDataAPI.refresh_getpos()
```

---

## API 文档

### `zbDataAPI.register_player_info_callback(func, list=[]) -> None`

自动回传玩家的 NBT 信息（位置、维度、朝向等）。
如果 `list` 为空（默认），监听所有NBT；否则仅对 `list` 中的NBT回传。

> **参数**
>
> - `func(name: str, info: dict)`：回调函数，`name` 是玩家名，`info` 是该玩家的最新信息字典。
> - `list: list`（可选）：要监听的NBT列表，默认 `[]`。

---

### `zbDataAPI.get_player_list() -> list`

获取当前所有在线玩家的名字列表。

```python
players = zbDataAPI.get_player_list()
```

---

### `zbDataAPI.register_player_list_callback(func) -> None`

当有玩家上线或下线时触发。

> **参数**
>
> - `func(player: str, current_list: list)`：回调函数，`player` 是发生变化的玩家名，`current_list` 是最新的在线玩家列表。

---

### `zbDataAPI.refresh_getpos() -> None`

手动触发一次玩家信息拉取，与内部定时拉取逻辑等效。

---

## 开发与贡献

1. Fork 本仓库
2. 新建分支 `feature/xxx`
3. 提交改动并发起 Pull Request

欢迎提交 issue 和 PR，让这个 API 更加完善！

---

## 许可协议

本项目遵循 GPLv3 许可，详情见 [LICENSE](./LICENSE) 文件。
