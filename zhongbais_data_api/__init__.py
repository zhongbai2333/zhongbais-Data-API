from zhongbais_data_api.entry import get_pos


class zbDataAPI(object):
    @staticmethod
    def get_player_info() -> dict:
        """
        获取玩家信息字典

        Get the dictionary of player info

        Returns:
            dict: 玩家信息 / Player information
        """
        return get_pos.player_info

    @staticmethod
    def register_player_info_callback(func) -> None:
        """
        注册回调函数，在 player_info 发生变化时触发

        Register a callback, triggered when player_info changes

        Args:
            func (callable): 回调函数，接收参数 (name: str, info: dict)

                             The callback function, receives (name: str, info: dict)

        Returns:
            None
        """
        get_pos.player_info.register_callback(func)

    @staticmethod
    def get_player_list() -> list:
        """
        获取在线玩家列表

        Get the list of online players

        Returns:
            list: 玩家列表 / List of player names
        """
        return list(get_pos.player_info.keys())

    @staticmethod
    def register_player_list_callback(func) -> None:
        """
        注册回调函数，在玩家列表增减时触发

        Register a callback, triggered when the player list changes

        Args:
            func (callable): 回调函数，接收参数 (player_list: list)

                             The callback function, receives (player_list: list)

        Returns:
            None
        """
        get_pos.player_info.register_key_callback(func)

    @staticmethod
    def refresh_getpos() -> None:
        """
        手动刷新 player_info

        Manually refresh player_info

        Returns:
            None
        """
        get_pos.getpos_player()
