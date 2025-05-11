# zhongbais Data API

A MCDReforged–based player position retrieval and callback API. It encapsulates timed polling and callback mechanisms, making it easy for other plugins or scripts to uniformly access and subscribe to changes in player position, dimension, rotation, and more.

English | [简中](README_zh.md)

---

## Features

- **Timed Polling**: Automatically polls all online players’ NBT data via RCON at the configured interval  
- **Callback System**: Built-in lists of callbacks let you subscribe to specific NBT fields or to player list changes  

---

## Quick Start

```python
from mcdreforged.api.all import PluginServerInterface, new_thread
from zhongbais_data_api import zbDataAPI

def on_load(self, server: PluginServerInterface, old):
    # Listen for *all* NBT changes
    zbDataAPI.register_player_info_callback(self.on_player_update)
    # Or listen for specific NBT fields only:
    # zbDataAPI.register_player_info_callback(self.on_player_update, ['Pos', 'Dimension', ...])

    # Listen for player join/leave events
    zbDataAPI.register_player_list_callback(self.on_player_list_change)

def on_player_update(self, name: str, info: dict):
    """
    name: player’s name
    info: {
      "Pos": [...],         # position [x, y, z]
      "Rotation": [...],    # rotation [yaw, pitch]
      "Dimension": "...",   # dimension
      …                     # other fields as configured
    }
    """
    self.server.logger.info(f"[PlayerUpdate] {name} -> {info}")

def on_player_list_change(self, player: str, current_list: list):
    # player: name of the player who joined or left
    # current_list: list of all online players
    self.server.logger.info(f"[PlayerList] {player} changed, now: {current_list}")

# Manually trigger a data fetch (e.g. for testing)
zbDataAPI.refresh_getpos()
```

---

## API Documentation

### `zbDataAPI.register_player_info_callback(func, list=[]) -> None`

Automatically delivers NBT data (position, dimension, rotation, etc.) for players.
If `list` is empty (default), listens to *all* players; otherwise, only to the specified NBT fields.

> **Parameters**
>
> - `func(name: str, info: dict)`: callback function; `name` is the player’s name, `info` is a dict of the latest data.
> - `list: list` (optional): list of NBT field names to listen for, default `[]`.

---

### `zbDataAPI.get_player_list() -> list`

Returns the list of currently online player names.

```python
players = zbDataAPI.get_player_list()
```

---

### `zbDataAPI.register_player_list_callback(func) -> None`

Triggered when a player joins or leaves.

> **Parameters**
>
> - `func(player: str, current_list: list)`: callback function; `player` is the name of the joined/left player, `current_list` is the updated list of online players.

---

### `zbDataAPI.refresh_getpos() -> None`

Manually triggers a data fetch, equivalent to the internal timed polling.

---

## Development & Contribution

1. Fork this repository
2. Create a branch `feature/xxx`
3. Commit your changes and open a Pull Request

Contributions, issues, and PRs are welcome to make this API even better!

---

## License

This project is licensed under GPLv3. See [LICENSE](./LICENSE) for details.
