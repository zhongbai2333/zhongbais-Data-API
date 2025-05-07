# zhongbais Data API

A player location retrieval and callback API built on MCDReforged. It wraps timed polling, AFK detection, and more—making it easy for other plugins or scripts to access and subscribe to changes in player position, dimension, orientation, and AFK status.

English | [简中](README_zh.md)

---

## Features

- **Timed Polling**: Automatically fetch Pos/Dim/Rot data for all online players at the configured interval via RCON  
- **AFK Detection**: Automatically mark players as AFK based on a configurable timeout  
- **Callback Mechanism**: Built on `ObservableDict`, callbacks are triggered on data changes for easy integration  

---

## Quick Start

```python
from mcdreforged.api.all import PluginServerInterface, new_thread
from zhongbais_data_api import zbDataAPI

def on_load(self, server: PluginServerInterface, old):
    # Register a callback to log whenever a player's info updates
    zbDataAPI.register_player_info_callback(self.on_player_update)

def on_player_update(self, name: str, info: dict):
    """
    name: player's name
    info: {
        "position": [x, y, z],
        "rotation": [yaw, pitch],
        "dimension": "minecraft:overworld",
        "last_update_time": timestamp,
        "is_afk": bool
    }
    """
    self.server.logger.info(f"[PlayerUpdate] {name} -> {info}")
```

---

## API Reference

### `zbDataAPI.get_player_info() -> dict`

Returns a dictionary of all currently online players’ info, for example:

```python
{
  "Alice": {
    "position": [x, y, z],
    "rotation": [yaw, pitch],
    "dimension": "minecraft:overworld",
    "last_update_time": timestamp,
    "is_afk": False,
  },
  "Bob": { … },
  …
}
```

### `zbDataAPI.get_player_list() -> list`

Returns a list of names of all currently online players:

```python
["Alice", "Bob", …]
```

### `zbDataAPI.register_player_info_callback(func)`

Registers a callback `func(player_info: dict)`, triggered whenever any player’s **complete info** (Pos/Rot/Dim/AFK) changes.

- **Parameters**

  - `func(player_info)`:

    - `player_info`: the updated data dictionary

### `zbDataAPI.register_player_list_callback(func)`

Registers a callback `func(player_list: list)`, triggered when the online player list changes (joins or leaves).

- **Parameters**

  - `func(player_list)`:

    - `player_list`: the updated list of player names

### `zbDataAPI.refresh_getpos() -> None`

Manually triggers a poll, equivalent to calling the internal `get_pos.getpos_player()`.

---

## Development & Contribution

1. Fork this repository
2. Create a new branch `feature/xxx`
3. Commit your changes and open a Pull Request

Feel free to open issues and PRs to improve this API!

---

## License

This project is licensed under the GPLv3. See [LICENSE](./LICENSE) for details.
